import os
from types import SimpleNamespace
from unittest.mock import patch
import unittest

from tests import test_task_runtime as fixtures
from crew_algorithms.wildfire_alg.core.scheduled_event_release import event_for_step
from crew_algorithms.wildfire_alg.config.build_config import create_level_presets, update_config
from crew_algorithms.wildfire_alg.coordination.runtime import RuntimeBridge


class ScheduledEventReleaseTests(unittest.TestCase):
    def setUp(self):
        with patch.dict(os.environ, {'CREW_HT_WORKER_EVENT_REPORT': '0',
                                     'CREW_HT_LOCAL_EVENT_INFO': '0'}):
            fixtures.TaskRuntimeTests.setUp(self)

    def test_new_fire_follows_actual_civilian_release_not_configured_step(self):
        with patch.dict(os.environ, {'CREW_RESOURCE_SCHEDULING_FAMILY': 'commitment_event'}):
            levels = create_level_presets()
        name = 'FiveCiviliansAt80_75AfterOriginalFireDozerMovesThenFireAt80_80_WorkerReport'
        cfg = {}
        update_config(levels[name], 42, cfg)
        events = cfg['scheduled_events']
        self.assertEqual(len(events), 2)
        self.assertIsNone(event_for_step(events, 8, [], lambda _: False))
        first = event_for_step(events, 11, [], lambda _: True)
        self.assertEqual((first['timestep'], first['release_reason']), (11, 'condition_met'))
        self.assertIsNone(event_for_step(events, 14, [first], lambda _: True))
        second = event_for_step(events, 17, [first], lambda _: True)
        self.assertEqual((second['timestep'], second['action']), (17, 'start_fire'))
        self.assertIsNone(event_for_step(events, 18, [first, second], lambda _: True))

    def test_no_committed_dozer_has_labelled_fallback(self):
        with patch.dict(os.environ, {'CREW_RESOURCE_SCHEDULING_FAMILY': 'commitment_event'}):
            events = create_level_presets()[
                'FiveCiviliansAt80_75AfterOriginalFireDozerMovesThenFireAt80_80_OrganizerDirect']['scheduled_events']
        fallback = event_for_step(events, 18, [], lambda _: False)
        self.assertEqual(fallback['release_reason'], 'fallback_latest_timestep')
        self.assertEqual(event_for_step(events, 24, [fallback], lambda _: False)['action'], 'start_fire')

    def test_commitment_requires_returned_movement_and_unfinished_initial_rescue(self):
        event = {'release_condition': 'original_fire_dozer_moved_and_initial_rescue_unfinished'}
        self.bridge.graph.world.update(fire_active=True, rewards=[0] * 13)
        self.bridge.graph.world['nodes']['9'] = {
            'online': True, 'facts': {'agent_type': 1}, 'position': [62, 20]}
        self.assertFalse(self.bridge.event_release_ready(event))
        self.bridge.original_fire_dozer_moved = True
        self.assertTrue(self.bridge.event_release_ready(event))
        self.bridge.graph.world['rewards'][5] = 5
        self.assertFalse(self.bridge.event_release_ready(event))

    def test_returned_dozer_motion_records_old_work_commitment(self):
        self.bridge.step = 7
        before = {'online': True, 'position': [62, 20], 'facts': {'agent_type': 1}}
        self.bridge.c.nodes['9'] = {'online': True, 'position': [60, 21],
                                    'facts': {'agent_type': 1}}
        self.bridge.graph.active['9'] = 'original_fire'
        self.bridge.runtime_agents['9'] = SimpleNamespace(past_actions=[])
        self.bridge.pending_actions = {'9': (None, [0, 23, 51], before)}
        with patch.object(RuntimeBridge, 'after_step'):
            self.bridge.after_step({}, [], {}, {'submitted_events': []})
        self.assertTrue(self.bridge.original_fire_dozer_moved)


if __name__ == '__main__':
    unittest.main()
