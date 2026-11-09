"""The new worker-first condition must keep the official location out of the center."""
import json
import os
import unittest
from unittest.mock import patch

from tests import test_task_runtime as fixtures
from crew_algorithms.wildfire_alg.coordination.runtime import RuntimeBridge


class WorkerEventReportTests(unittest.TestCase):
    def setUp(self):
        with patch.dict(os.environ, {'CREW_HT_WORKER_EVENT_REPORT': '1',
                                     'CREW_HT_LOCAL_EVENT_INFO': '0'}):
            fixtures.TaskRuntimeTests.setUp(self)

    def test_distant_worker_receives_full_event_without_center_notice(self):
        event = {'timestep': 8, 'action': 'start_fire', 'x': 80, 'y': 80,
                 'announcement': 'A new fire was reported at (80,80).'}
        self.bridge.step = 8
        self.bridge.c.nodes = {
            '1': {'online': True, 'position': [1, 1], 'facts': {'agent_type': 0}},
            '2': {'online': True, 'position': [2, 1], 'facts': {'agent_type': 2}},
            '3': {'online': True, 'position': [3, 1], 'facts': {'agent_type': 0}},
        }
        with patch.object(RuntimeBridge, 'after_step'):
            self.bridge.after_step({}, list(self.agents.values()), {}, {'submitted_events': [event]})
        self.assertEqual(self.bridge.graph.environment_notices, [])
        self.assertEqual(len(self.agents['2'].chat_history['ENVIRONMENT']), 1)
        self.assertIn('80,80', self.agents['2'].chat_history['ENVIRONMENT'][0][1])
        self.assertNotIn('ENVIRONMENT', self.agents['1'].chat_history)
        self.assertNotIn('80', json.dumps(self.bridge.graph.decision_state()))
        self.assertIn('REPORT', self.bridge.communication_prompt('2', 'Communicate'))
        delivered = [e for e in self.bridge.c.events
                     if e['event_type'] == 'TASK_WORKER_EVENT_REPORT_DELIVERED']
        self.assertEqual(delivered[-1]['payload']['recipient'], '2')

    def test_single_civilian_report_reaches_worker_without_radius_limit(self):
        event = {'timestep': 8, 'action': 'spawn_civilian', 'x': 80, 'y': 20,
                 'announcement': 'One civilian was reported at (80,20).'}
        self.bridge.step = 8
        self.bridge.c.nodes = {
            '1': {'online': True, 'position': [1, 1], 'facts': {'agent_type': 0}},
            '2': {'online': True, 'position': [2, 1], 'facts': {'agent_type': 2}},
            '3': {'online': True, 'position': [3, 1], 'facts': {'agent_type': 0}},
        }
        with patch.object(RuntimeBridge, 'after_step'):
            self.bridge.after_step({}, list(self.agents.values()), {}, {'submitted_events': [event]})
        self.assertEqual(self.bridge.graph.environment_notices, [])
        self.assertIn('80,20', self.agents['3'].chat_history['ENVIRONMENT'][0][1])
