"""Static/fake checks: official shared policy errors precede every side effect."""
import unittest
from dataclasses import FrozenInstanceError
from functools import partial, wraps

from expgym.execution_contract import UNBOUND
from expgym.extras.parallel_cache import (
    AgentClock, SharedExplorationGraph, SharedExplorationLedger,
    SharedObservationCache, make_graph_augmenter, make_ledger_augmenter,
    make_pre_tool_hook, wrap_tools_with_cache, wrap_tools_with_ledger,
    wrap_tools_with_polact, wrap_tools_with_poolact,
)
from expgym.poolact import PoolActCoordinator
from expgym.react_loop import LLMOutput, run_react_loop


class Replay:
    def __init__(self):
        self.inputs = []

    def generate(self, messages):
        self.inputs.append(messages)
        return LLMOutput('Action: evaluate_config {"x":1}' if len(self.inputs) == 1
                         else 'Answer: {"x":1}')


def runtime_args(runtime):
    return dict(tools=runtime.tools, agent_clock=runtime.clock,
                observation_augmenter=runtime.observation_augmenter,
                pre_tool_hook=runtime.pre_tool_hook, llm_lock=runtime.reasoning_lock)


class ExecutionContractTest(unittest.TestCase):
    def setUp(self):
        self.tool_calls = []

    def tool(self, payload):
        self.tool_calls.append(payload)
        return .765432, 10.

    def assert_rejected(self, *, fragment='Execution contract', **kwargs):
        llm = Replay()
        with self.assertRaisesRegex(ValueError, fragment):
            run_react_loop(llm=llm, context='Tune x.', **kwargs)
        self.assertEqual([], llm.inputs)
        self.assertEqual([], self.tool_calls)

    def test_missing_budget_rejected_before_graph_claim_or_model(self):
        coordinator = PoolActCoordinator(1)
        runtime = coordinator.bind_tools({'evaluate_config': self.tool}, 0)
        self.assert_rejected(**runtime_args(runtime), time_budget=10.)
        self.assertEqual(0, runtime.clock.now)
        self.assertEqual(0, coordinator.cache.stats()['size'])
        self.assertEqual(0, coordinator.graph.stats()['total_visits'])
        self.assertEqual(0, coordinator.graph.stats()['pending_claims'])

    def test_scale_mismatch_rejected(self):
        runtime = PoolActCoordinator(1).bind_tools(
            {'evaluate_config': self.tool}, 0, time_budget=10., overhead_scale=.5)
        self.assert_rejected(**runtime_args(runtime), time_budget=10., overhead_scale=1.)

    def test_none_is_not_a_wildcard_in_either_direction(self):
        for bound, loop in ((None, 10.), (10., None), (0., None), (0., 1.)):
            with self.subTest(bound=bound, loop=loop):
                runtime = PoolActCoordinator(1).bind_tools({}, 0, time_budget=bound)
                self.assert_rejected(**runtime_args(runtime), time_budget=loop)

    def test_same_values_match_without_isclose(self):
        runtime = PoolActCoordinator(1).bind_tools({}, 0, time_budget=10.)
        self.assert_rejected(**runtime_args(runtime), time_budget=10.00000000001)

    def test_missing_or_different_clock_rejected_even_when_unlimited(self):
        runtime = PoolActCoordinator(1).bind_tools({'evaluate_config': self.tool}, 0)
        for clock in (None, AgentClock()):
            with self.subTest(clock=clock):
                args = runtime_args(runtime)
                args['agent_clock'] = clock
                self.assert_rejected(**args, fragment='agent_clock identity')

    def test_matching_boundary_still_withheld_without_clock_recount(self):
        for scale, raw_cost in ((1., 10.), (2., 5.)):
            coordinator = PoolActCoordinator(1)
            runtime = coordinator.bind_tools(
                {'evaluate_config': lambda _: (.765432, raw_cost)}, 0,
                time_budget=10., overhead_scale=scale)
            llm = Replay()
            result = run_react_loop(llm, context='Tune x.', max_steps=2,
                                    time_budget=10., overhead_scale=scale,
                                    **runtime_args(runtime))
            self.assertEqual(10., result['total_overhead'])
            self.assertEqual(10., runtime.clock.now)
            self.assertEqual([], result['eval_records'])
            self.assertEqual(2, len(llm.inputs))
            self.assertNotIn('765432', str(llm.inputs[-1]))
            self.assertEqual(0, coordinator.cache.stats()['size'])
            self.assertEqual(0, coordinator.graph.stats()['total_visits'])

    def test_matched_free_policy_keeps_cost_free_feedback(self):
        runtime = PoolActCoordinator(1).bind_tools({'evaluate_config': self.tool}, 0,
                                                  time_budget=10., overhead_scale=0.)
        result = run_react_loop(Replay(), time_budget=10., overhead_scale=0.,
                                max_steps=2, **runtime_args(runtime))
        self.assertEqual(0., result['total_overhead'])
        self.assertEqual(1, result['evaluations'])

    def test_plain_tools_with_unbound_clock_remain_compatible(self):
        for clock in (None, AgentClock()):
            result = run_react_loop(Replay(), {'evaluate_config': self.tool},
                                    agent_clock=clock, time_budget=10., max_steps=2)
            self.assertEqual(10., result['total_overhead'])
            if clock is not None:
                self.assertEqual(10., clock.now)
                self.assertFalse(hasattr(clock, '__expgym_execution_contract__'))

    def test_explicit_clock_binding_is_immutable_and_optional(self):
        clock = AgentClock()
        clock.bind_execution_policy(time_budget=10, overhead_scale=2)
        clock.bind_execution_policy(time_budget=10., overhead_scale=2.)
        policy = clock.__expgym_execution_contract__
        with self.assertRaises(FrozenInstanceError):
            policy.time_budget = 20.
        with self.assertRaisesRegex(ValueError, 'time_budget mismatch'):
            clock.bind_execution_policy(time_budget=None, overhead_scale=2.)
        self.assertIs(policy, clock.__expgym_execution_contract__)
        self.assertEqual(0, clock.now)
        self.assert_rejected(tools={}, agent_clock=clock, time_budget=10.)

    def test_augmenter_can_bind_budget_before_wrapper_binds_scale(self):
        clock = AgentClock()
        graph = SharedExplorationGraph()
        augmenter = make_graph_augmenter(graph, clock=clock, time_budget=10.)
        self.assertIs(clock.__expgym_execution_contract__.overhead_scale, UNBOUND)
        tools = wrap_tools_with_poolact({'evaluate_config': self.tool},
                                        SharedObservationCache(), graph, 0,
                                        clock=clock, time_budget=10., overhead_scale=0.)
        run_react_loop(Replay(), tools, agent_clock=clock, observation_augmenter=augmenter,
                       time_budget=10., overhead_scale=0., max_steps=2)
        self.assertEqual(0., clock.now)

    def test_augmenter_conflict_is_rejected_at_construction(self):
        clock = AgentClock()
        clock.bind_execution_policy(time_budget=10.)
        before = clock.__expgym_execution_contract__
        with self.assertRaisesRegex(ValueError, 'time_budget mismatch'):
            make_graph_augmenter(SharedExplorationGraph(), clock=clock)
        self.assertIs(before, clock.__expgym_execution_contract__)

    def test_augmenter_and_hook_identity_are_checked_without_shared_tools(self):
        clock, other = AgentClock(), AgentClock()
        graph = SharedExplorationGraph()
        self.assert_rejected(tools={}, agent_clock=clock,
                             observation_augmenter=make_graph_augmenter(graph, clock=other))
        self.assert_rejected(tools={}, agent_clock=clock,
                             pre_tool_hook=make_pre_tool_hook(graph, 0, clock=other))

    def test_empty_wrappers_still_bind_the_supplied_clock(self):
        for kind in ('cached', 'poolact'):
            clock = AgentClock()
            if kind == 'cached':
                tools = wrap_tools_with_cache({}, SharedObservationCache(), clock=clock)
            else:
                tools = wrap_tools_with_poolact({}, SharedObservationCache(),
                                                SharedExplorationGraph(), 0, clock=clock)
            self.assert_rejected(tools=tools, agent_clock=clock, time_budget=10.)

    def test_cached_wrapper_contract_is_checked_even_if_clock_argument_omitted(self):
        tools = wrap_tools_with_cache({'evaluate_config': self.tool},
                                      SharedObservationCache(), clock=AgentClock(), time_budget=10.)
        self.assert_rejected(tools=tools, time_budget=10.)

    def test_clockless_shared_components_reject_finite_but_keep_unlimited(self):
        ledger = SharedExplorationLedger()
        graph = SharedExplorationGraph()
        variants = [
            (wrap_tools_with_cache({'evaluate_config': self.tool}, SharedObservationCache()), None),
            (wrap_tools_with_polact({'evaluate_config': self.tool}, SharedObservationCache(), graph, 0), None),
            (wrap_tools_with_ledger({'evaluate_config': self.tool}, SharedObservationCache(), ledger, 0),
             make_ledger_augmenter(ledger)),
            ({'evaluate_config': self.tool}, make_graph_augmenter(graph)),
        ]
        for tools, augmenter in variants:
            self.tool_calls.clear()
            self.assert_rejected(tools=tools, observation_augmenter=augmenter, time_budget=10.)
            result = run_react_loop(Replay(), tools, observation_augmenter=augmenter, max_steps=2)
            self.assertEqual(10., result['total_overhead'])

    def test_graph_augmenter_requires_clock_for_finite_budget(self):
        with self.assertRaisesRegex(ValueError, 'AgentClock'):
            make_graph_augmenter(SharedExplorationGraph(), time_budget=10.)

    def test_wrappers_do_not_half_bind_clock_on_conflict(self):
        first, second = AgentClock(), AgentClock()
        inner = wrap_tools_with_cache({'evaluate_config': self.tool}, SharedObservationCache(),
                                      clock=first, time_budget=10.)
        for constructor in (
                lambda: wrap_tools_with_cache(inner, SharedObservationCache(), clock=second, time_budget=10.),
                lambda: wrap_tools_with_poolact(inner, SharedObservationCache(), SharedExplorationGraph(),
                                                0, clock=second, time_budget=10.)):
            with self.assertRaisesRegex(ValueError, 'agent_clock identity'):
                constructor()
            self.assertFalse(hasattr(second, '__expgym_execution_contract__'))

    def test_transparent_wrappers_and_partial_cannot_hide_contract(self):
        inner = wrap_tools_with_cache({'evaluate_config': self.tool}, SharedObservationCache())['evaluate_config']

        @wraps(inner)
        def decorated(payload):
            return inner(payload)

        del decorated.__expgym_execution_contract__  # __wrapped__ still retains it
        for tool in (decorated, partial(inner)):
            self.assert_rejected(tools={'evaluate_config': tool}, time_budget=10.)

    def test_protocol_and_forced_final_both_reject_before_backend_or_hooks(self):
        runtime = PoolActCoordinator(1).bind_tools({'evaluate_config': self.tool}, 0)
        for protocol in ('native', 'text'):
            self.assert_rejected(**runtime_args(runtime), time_budget=10., max_steps=0,
                                 tool_protocol=protocol)

    def test_bad_explicit_policies_are_not_installed(self):
        for field in ('time_budget', 'overhead_scale'):
            for value in (True, -1., float('nan'), float('inf')):
                clock = AgentClock()
                with self.assertRaises(ValueError):
                    clock.bind_execution_policy(**{field: value})
                self.assertFalse(hasattr(clock, '__expgym_execution_contract__'))


if __name__ == '__main__':
    unittest.main()
