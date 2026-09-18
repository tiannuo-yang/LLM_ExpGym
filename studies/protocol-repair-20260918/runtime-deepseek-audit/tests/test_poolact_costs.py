"""Invalid simulator costs are errors, never free or future feedback."""
import threading
import unittest
from unittest.mock import patch

from expgym.poolact import AgentClock, PoolActCoordinator, run_agents_parallel
from expgym.extras.parallel_cache import (
    SharedObservationCache, wrap_tools_with_cache,
)


class PoolActCostValidationTest(unittest.TestCase):
    def test_clock_rejects_invalid_increment_without_mutation(self):
        clock = AgentClock()
        clock.advance(2.)
        for invalid in (-1., float('nan'), float('inf'), -float('inf'), None, True):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    clock.advance(invalid)
                self.assertEqual(2., clock.now)

    def test_clock_accumulation_overflow_is_not_persisted(self):
        clock = AgentClock()
        clock.advance(1e308)
        with self.assertRaisesRegex(ValueError, 'accumulated clock'):
            clock.advance(1e308)
        self.assertEqual(1e308, clock.now)

    def test_invalid_cost_or_shape_never_publishes_and_closes_claim(self):
        invalid_returns = [
            ('output', -1.), ('output', float('nan')), ('output', float('inf')),
            ('output', None), ('output', True), ('output', '1'),
            ('output', .2, -1.), ('output', .2, float('inf')),
            None, 'bare output', ('one',), ('a', 'b', 'c', 'd'),
        ]
        for tool_return in invalid_returns:
            with self.subTest(tool_return=tool_return):
                coordinator = PoolActCoordinator(1)
                runtime = coordinator.bind_tools({'lookup': lambda payload: tool_return}, 0)
                runtime.pre_tool_hook('lookup', '{}')
                with self.assertRaises(ValueError):
                    runtime.tools['lookup']('{}')
                self.assertEqual(0, coordinator.graph.stats()['pending_claims'])
                self.assertEqual(0, coordinator.graph.stats()['total_visits'])
                self.assertEqual(0, coordinator.cache.stats()['size'])
                self.assertEqual(0., runtime.clock.now)

    def test_cached_strategy_rejects_invalid_cost_without_publish(self):
        for invalid in (-1., float('nan'), float('inf')):
            cache = SharedObservationCache()
            wrapped = wrap_tools_with_cache({'lookup': lambda payload: ('bad', invalid)}, cache)
            with self.assertRaises(ValueError):
                wrapped['lookup']('{}')
            self.assertEqual(0, cache.stats()['size'])

    def test_bad_cached_cost_cannot_be_zeroed_into_valid_feedback(self):
        coordinator = PoolActCoordinator(1)
        coordinator.cache.put('lookup', '{}', ('bad', float('nan')))
        runtime = coordinator.bind_tools({'lookup': lambda payload: ('new', 1.)}, 0)
        runtime.pre_tool_hook('lookup', '{}')
        with self.assertRaises(ValueError):
            runtime.tools['lookup']('{}')
        self.assertEqual(0, coordinator.graph.stats()['pending_claims'])
        self.assertEqual(0, coordinator.graph.stats()['total_visits'])

    def test_invalid_scale_and_budget_rejected_at_binding(self):
        for invalid in (-1., float('nan'), float('inf'), True):
            for parameter in ('overhead_scale', 'time_budget'):
                with self.subTest(parameter=parameter, invalid=invalid):
                    with self.assertRaises(ValueError):
                        PoolActCoordinator(1).bind_tools({}, 0, **{parameter: invalid})
                    with self.assertRaises(ValueError):
                        wrap_tools_with_cache({}, SharedObservationCache(), clock=AgentClock(),
                                              **{parameter: invalid})

    def test_scale_and_completion_overflow_close_claim_without_publish(self):
        for scale, start in ((2., 0.), (1., 1e308)):
            coordinator = PoolActCoordinator(1)
            runtime = coordinator.bind_tools({'lookup': lambda payload: ('ok', 1e308)},
                                             0, overhead_scale=scale)
            runtime.clock.advance(start)
            runtime.pre_tool_hook('lookup', '{}')
            with self.assertRaises(ValueError):
                runtime.tools['lookup']('{}')
            self.assertEqual(0, coordinator.graph.stats()['pending_claims'])
            self.assertEqual(0, coordinator.cache.stats()['size'])
            self.assertEqual(start, runtime.clock.now)

    def test_cache_timestamp_rejects_nonfinite_and_negative(self):
        cache = SharedObservationCache()
        for invalid in (-1., float('nan'), float('inf')):
            with self.assertRaises(ValueError):
                cache.put('lookup', '{}', ('ok', 1.), completion_time=invalid)
        self.assertEqual(0, cache.stats()['size'])

    def test_invalid_visibility_cannot_disable_time_gate(self):
        graph = PoolActCoordinator(1).graph
        graph.record_evaluate_config(0, '{}', '{}', .9, 10., completion_time=10.)
        for invalid in (-1., float('nan'), float('inf')):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    graph.format_for_injection(visible_before=invalid)
                with self.assertRaises(ValueError):
                    graph.format_for_injection(completion_before=invalid)
                with self.assertRaises(ValueError):
                    graph.get_visible_pending(visible_at=invalid)
                with self.assertRaises(ValueError):
                    graph.is_in_progress_by_other('lookup', '{}', 1, visible_at=invalid)

    def test_cache_or_graph_exception_cleans_pre_tool_claim(self):
        for method in ('get', 'put', 'graph'):
            coordinator = PoolActCoordinator(1)
            runtime = coordinator.bind_tools({'search': lambda payload: ('Article: A', 1.)}, 0)
            runtime.pre_tool_hook('search', '{"query":"q"}')
            target = (patch.object(coordinator.cache, method, side_effect=RuntimeError(method))
                      if method != 'graph' else patch(
                          'expgym.extras.parallel_cache._record_in_graph',
                          side_effect=RuntimeError(method)))
            with target, self.assertRaisesRegex(RuntimeError, method):
                runtime.tools['search']('{"query":"q"}')
            self.assertEqual(0, coordinator.graph.stats()['pending_claims'])

    def test_base_exception_closes_claim_and_is_not_transformed(self):
        class StopNow(BaseException):
            pass

        def stop(payload):
            raise StopNow('stop')

        coordinator = PoolActCoordinator(1)
        runtime = coordinator.bind_tools({'lookup': stop}, 0)
        runtime.pre_tool_hook('lookup', '{}')
        with self.assertRaises(StopNow):
            runtime.tools['lookup']('{}')
        self.assertEqual(0, coordinator.graph.stats()['pending_claims'])
        self.assertEqual(0, coordinator.cache.stats()['size'])

    def test_parallel_error_closes_all_entered_tool_claims(self):
        coordinator = PoolActCoordinator(2)
        barrier = threading.Barrier(2, timeout=3.)

        def run_agent(agent_id):
            def tool(payload):
                barrier.wait()
                if agent_id == 0:
                    return ('bad', float('nan'))
                return ('ok', 1.)
            runtime = coordinator.bind_tools({'lookup': tool}, agent_id)
            runtime.pre_tool_hook('lookup', '{}')
            return {'tool_result': runtime.tools['lookup']('{}')}

        with self.assertRaises(ValueError):
            run_agents_parallel(2, run_agent)
        self.assertEqual(0, coordinator.graph.stats()['pending_claims'])
        self.assertEqual(1, coordinator.cache.stats()['size'])

    def test_agent_cleanup_is_idempotent_and_does_not_close_other_agents(self):
        graph = PoolActCoordinator(2).graph
        graph.record_claim('lookup', '{}', 0, start_time=2.)
        graph.record_claim('lookup', '{}', 1, start_time=2.)
        graph.record_claim('lookup', '{"done":1}', 0, start_time=1.)
        graph.complete_claim('lookup', '{"done":1}', 0, completion_time=3.)
        self.assertEqual(1, graph.complete_agent_claims(0, completion_time=2.))
        self.assertEqual(0, graph.complete_agent_claims(0, completion_time=9.))
        self.assertEqual(1, graph.stats()['pending_claims'])
        self.assertTrue(graph.has_pending_claim('lookup', '{}', 1))
        self.assertEqual(0, graph.stats()['total_visits'])
        # The earlier completed claim still completes at 3, not cleanup time 9.
        visible = graph.get_visible_pending(visible_at=2.5)
        self.assertTrue(any(claim.display == 'lookup {done=1}' for claim in visible))


if __name__ == '__main__':
    unittest.main()
