"""Dynamic fire completion follows the original ORCH second-fire rule."""
import os
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'ORCH/crew-algorithms'))
from crew_algorithms.wildfire_alg.core.alg_utils import check_game_done
from crew_algorithms.wildfire_alg.core.alg_utils import write_task_outcome
import tempfile


class ResourceBenchmarkSuccessTests(unittest.TestCase):
    def test_combined_task_waits_for_event_but_not_unreachable_rescue_count(self):
        event = {'timestep': 8, 'action': 'spawn_civilians_5', 'x': 80, 'y': 75}
        cfg = SimpleNamespace(game_type=5, civilian_count=5, civilian_clusters=1,
                              scheduled_events=[event])
        data = {'rewards': [0]*13, 'game_data': {'fire_active': False},
                'fire_ever_active': True, 'civilian_target': 10,
                'submitted_events': []}
        with patch.dict(os.environ, {'CREW_RESOURCE_SCHEDULING_FAMILY': 'commitment_event'}):
            self.assertFalse(check_game_done(data, cfg, 0))
            data['submitted_events'] = [event]
            self.assertTrue(check_game_done(data, cfg, 0))
            data['game_data']['fire_active'] = True
            self.assertFalse(check_game_done(data, cfg, 0))
            data['game_data']['fire_active'] = False
            data['score'] = 0
            with tempfile.TemporaryDirectory() as directory:
                outcome = write_task_outcome(data, cfg, directory)
            self.assertEqual(outcome['success_scope'], 'fire_control_only')
            self.assertFalse(outcome['civilian_rescue_scored'])

    def test_fire_task_waits_for_later_fire(self):
        event = {'event_id': 'second_fire', 'timestep': 8, 'action': 'start_fire',
                 'x': 80, 'y': 80}
        cfg = SimpleNamespace(game_type=3, scheduled_events=[event])
        data = {'rewards': [0]*13, 'game_data': {'fire_active': False},
                'fire_ever_active': True, 'submitted_events': []}
        with patch.dict(os.environ, {'CREW_RESOURCE_SCHEDULING_FAMILY': 'focused'}):
            self.assertFalse(check_game_done(data, cfg, 0))
            data['submitted_events'] = [{**event, 'timestep': 9,
                                         'configured_timestep': 8}]
            self.assertTrue(check_game_done(data, cfg, 0))


if __name__ == '__main__':
    unittest.main()
