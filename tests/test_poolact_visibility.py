"""No-model regression coverage for shared simulated-time visibility."""
import unittest

from expgym.poolact import AgentClock, PoolActCoordinator, SharedExplorationGraph
from expgym.extras.parallel_cache import (
    SharedObservationCache, SharedExplorationLedger, wrap_tools_with_cache,
    wrap_tools_with_ledger, wrap_tools_with_polact,
)
from expgym.react_loop import LLMOutput, run_react_loop


class GraphVisibilityTest(unittest.TestCase):
    def test_later_eval_cannot_change_earlier_visible_score_or_visitors(self):
        graph = SharedExplorationGraph(diversity_mode=True)
        graph.record_evaluate_config(0, '{}', '{}', .1, 5, completion_time=5)
        graph.record_evaluate_config(1, '{}', '{}', .9, 10, completion_time=20)
        early = graph.format_for_injection(visible_before=5, agent_id=2)
        self.assertIn('0.100000', early)
        self.assertNotIn('0.900000', early)
        self.assertIn('[agents 0]', early)
        self.assertNotIn('[agents 0,1]', early)
        self.assertIn('0.900000', graph.format_for_injection(visible_before=20))

    def test_later_search_results_and_visit_counts_are_hidden(self):
        graph = SharedExplorationGraph()
        graph.record_search_meta(0, 'q', [1], completion_time=1)
        graph.record_search_meta(1, 'q', [1, 2, 3], completion_time=10)
        early = graph.format_for_injection(visible_before=1)
        self.assertIn('returned_docs=[1]', early)
        self.assertIn('visited_by=[0]  visits=1', early)
        self.assertNotIn('returned_docs=[1,2,3]', early)

    def test_physically_first_future_fetch_does_not_supply_early_content(self):
        graph = SharedExplorationGraph()
        graph.record_fetch_doc(1, 1, 'future', 'future content', completion_time=10)
        graph.record_fetch_doc(0, 1, 'early', 'early content', completion_time=1)
        early = graph.format_for_injection(visible_before=1)
        self.assertIn('early content', early)
        self.assertNotIn('future', early)

    def test_future_edge_hidden_even_when_both_endpoints_already_exist(self):
        graph = SharedExplorationGraph(diversity_mode=True)
        graph.record_search(0, 'a', 'A', completion_time=1)
        graph.record_search(1, 'b', 'B', completion_time=1)
        graph.record_search(2, 'a', 'A', completion_time=10)
        graph.record_search(2, 'b', 'B', completion_time=20)
        early = graph.format_for_injection(visible_before=1)
        self.assertNotIn('-->', early)
        self.assertNotIn('[agents 0,2]', early)
        self.assertIn('-->', graph.format_for_injection(visible_before=20))

    def test_completion_boundary_is_inclusive_but_budget_is_strict(self):
        graph = SharedExplorationGraph(diversity_mode=True)
        graph.record_search(0, 'at-boundary', 'A', completion_time=10)
        self.assertIn('at-boundary', graph.format_for_injection(visible_before=10))
        self.assertEqual('', graph.format_for_injection(
            visible_before=20, completion_before=10,
        ))

    def test_completed_claim_not_pending_in_unbounded_view(self):
        graph = SharedExplorationGraph(diversity_mode=True)
        graph.record_claim('search', '{"query":"q"}', 0, start_time=1)
        graph.complete_claim('search', '{"query":"q"}', 0, completion_time=10)
        self.assertEqual([], graph.get_visible_pending())
        self.assertFalse(graph.is_in_progress_by_other('search', '{"query":"q"}', 1))
        self.assertEqual(1, len(graph.get_visible_pending(visible_at=5)))
        self.assertEqual([], graph.get_visible_pending(visible_at=10))
        self.assertEqual([], graph.get_visible_pending(visible_at=0))

    def test_pending_claim_is_not_feedback_or_coverage(self):
        graph = SharedExplorationGraph(diversity_mode=True)
        graph.record_claim('evaluate_config', '{"x":1}', 0)
        text = graph.format_for_injection(visible_before=0, agent_id=1)
        self.assertIn('In Progress', text)
        self.assertIn('None completed yet.', text)
        self.assertNotIn('unique configs evaluated', text)
        self.assertEqual(0, graph.stats()['total_visits'])


class BudgetPublicationTest(unittest.TestCase):
    def test_budget_requires_explicit_clock(self):
        with self.assertRaisesRegex(ValueError, 'AgentClock'):
            wrap_tools_with_cache({}, SharedObservationCache(), time_budget=10.)

    def test_cached_future_miss_pays_once_then_eligible_hit_is_zero(self):
        cache = SharedObservationCache()
        cache.put('lookup', '{}', ('first', 5.), completion_time=10.)
        clock = AgentClock()
        calls = []

        def original(payload):
            calls.append(payload)
            return ('second', 5.)

        tools = wrap_tools_with_cache({'lookup': original}, cache, clock=clock,
                                      overhead_scale=2., time_budget=20.)
        self.assertEqual(('second', 5.), tools['lookup']('{}'))
        self.assertEqual(0., clock.now)
        clock.advance(10.)
        self.assertEqual(('first', 0.), tools['lookup']('{}'))
        self.assertEqual(['{}'], calls)
        self.assertEqual({'hits': 1, 'misses': 1, 'size': 1}, cache.stats())

    def test_cache_strict_ceiling_even_when_observer_clock_is_later(self):
        cache = SharedObservationCache()
        cache.put('lookup', '{}', ('future', 10.), completion_time=10.)
        self.assertIsNone(cache.get('lookup', '{}', visible_before=20., completion_before=10.))

    def test_boundary_result_retained_for_caller_but_not_shared(self):
        for overhead in (10., 11.):
            with self.subTest(overhead=overhead):
                coordinator = PoolActCoordinator(2)
                runtime = coordinator.bind_tools(
                    {'evaluate_config': lambda payload: (.765432, overhead)},
                    0, time_budget=10,
                )
                runtime.pre_tool_hook('evaluate_config', '{}')
                self.assertEqual((.765432, overhead), runtime.tools['evaluate_config']('{}'))
                self.assertEqual(0, coordinator.cache.stats()['size'])
                self.assertEqual(0, coordinator.graph.stats()['eval_nodes'])
                self.assertEqual(0, coordinator.graph.stats()['pending_claims'])
                self.assertEqual(0, runtime.clock.now)  # loop, not wrapper, advances

    def test_publication_uses_scaled_simulated_seconds(self):
        coordinator = PoolActCoordinator(1)
        runtime = coordinator.bind_tools(
            {'evaluate_config': lambda payload: (.5, 5.)},
            0, time_budget=10., overhead_scale=2.,
        )
        runtime.tools['evaluate_config']('{}')
        self.assertEqual(0, coordinator.cache.stats()['size'])
        self.assertEqual(0, runtime.clock.now)

    def test_free_completed_result_is_visible_and_zero_cost_cache_hit(self):
        coordinator = PoolActCoordinator(2)
        first = coordinator.bind_tools({'search': lambda payload: ('Article: A', 10.)},
                                       0, overhead_scale=0.)
        second = coordinator.bind_tools({'search': lambda payload: ('Article: B', 10.)},
                                        1, overhead_scale=0.)
        first.tools['search']('{"query":"q"}')
        self.assertEqual(('Article: A', 0.), second.tools['search']('{"query":"q"}'))
        self.assertEqual(0, first.clock.now)
        self.assertEqual(0, second.clock.now)

    def test_cached_strategy_also_does_not_publish_boundary_results(self):
        cache = SharedObservationCache()
        clock = AgentClock()
        tools = wrap_tools_with_cache({'lookup': lambda payload: ('withheld', 5.)},
                                      cache, clock=clock, overhead_scale=2., time_budget=10.)
        self.assertEqual(('withheld', 5.), tools['lookup']('{}'))
        self.assertEqual(0, cache.stats()['size'])

    def test_force_final_cannot_recover_withheld_feedback_from_graph(self):
        class FakeLLM:
            def __init__(self):
                self.inputs = []

            def generate(self, messages):
                self.inputs.append([dict(message) for message in messages])
                return LLMOutput('Action: evaluate_config {"x":1}' if len(self.inputs) == 1
                                 else 'Answer: {"x":1}')

        coordinator = PoolActCoordinator(1)
        runtime = coordinator.bind_tools(
            {'evaluate_config': lambda payload: (.765432, 10.)}, 0, time_budget=10.,
        )
        llm = FakeLLM()
        result = run_react_loop(
            llm=llm, tools=runtime.tools, context='Tune x.', max_steps=2,
            time_budget=10., observation_augmenter=runtime.observation_augmenter,
            agent_clock=runtime.clock, pre_tool_hook=runtime.pre_tool_hook,
            llm_lock=runtime.reasoning_lock,
        )
        self.assertEqual(10., result['total_overhead'])
        self.assertEqual(10., runtime.clock.now)
        self.assertIn('withheld', str(llm.inputs[-1]))
        self.assertNotIn('765432', str(llm.inputs[-1]))

    def test_viewer_budget_hides_other_agents_later_feedback(self):
        coordinator = PoolActCoordinator(2)
        runtime = coordinator.bind_tools({}, 0, time_budget=5.)
        coordinator.graph.record_evaluate_config(1, '{}', '{}', .765432, 10,
                                                 completion_time=10.)
        runtime.clock.advance(20.)
        self.assertNotIn('765432', runtime.observation_augmenter('withheld'))

    def test_tool_schema_metadata_survives_every_wrapper(self):
        def original(payload):
            return ('ok', 1.)

        schema = {'type': 'function', 'function': {'name': 'lookup', 'parameters': {'type': 'object'}}}
        original.__expgym_tool_schema__ = schema
        coordinator = PoolActCoordinator(1)
        variants = [
            wrap_tools_with_cache({'lookup': original}, SharedObservationCache()),
            wrap_tools_with_ledger({'lookup': original}, SharedObservationCache(),
                                   SharedExplorationLedger(), 0),
            coordinator.bind_tools({'lookup': original}, 0).tools,
            wrap_tools_with_polact({'lookup': original}, SharedObservationCache(),
                                   SharedExplorationGraph(), 0),
        ]
        for variant in variants:
            self.assertEqual(schema, variant['lookup'].__expgym_tool_schema__)
            self.assertEqual(original.__name__, variant['lookup'].__name__)


if __name__ == '__main__':
    unittest.main()
