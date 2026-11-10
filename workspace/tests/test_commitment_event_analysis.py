"""A goal rewrite must not count as a membership change."""
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from analyze_commitment_event_run import analyze


class CommitmentEventAnalysisTests(unittest.TestCase):
    def test_repeated_topology_is_not_a_new_reorganization(self):
        def record(kind, payload):
            return {'event_type': kind, 'payload': payload, 'agent_id': None}

        rows = [record('TASK_WORLD_SNAPSHOT', {'step': 0, 'phase': 'before_action', 'nodes': {}}),
                record('TASK_GRAPH_COMMITTED', {'edges': [
                    {'id': 'fire', 'members': ['1', '2'], 'leader': '1'}]}),
                record('TASK_WORLD_SNAPSHOT', {'step': 9, 'phase': 'before_action', 'nodes': {}}),
                record('TASK_GRAPH_COMMITTED', {'edges': [
                    {'id': 'fire', 'members': ['1', '2'], 'leader': '1', 'goal': 'new goal'}]}),
                record('TASK_WORLD_SNAPSHOT', {'step': 15, 'phase': 'before_action', 'nodes': {}}),
                record('TASK_GRAPH_COMMITTED', {'edges': [
                    {'id': 'fire', 'members': ['1', '2', '3'], 'leader': '1'}]})]
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'events.jsonl'
            path.write_text(''.join(json.dumps(row) + '\n' for row in rows))
            result = analyze(path)
        self.assertEqual(result['first_topology_change_step'], 15)


if __name__ == '__main__':
    unittest.main()
