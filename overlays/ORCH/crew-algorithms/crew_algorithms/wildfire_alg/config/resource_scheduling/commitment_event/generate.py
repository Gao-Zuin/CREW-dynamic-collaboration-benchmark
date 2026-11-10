"""A matched event pair released after the original-fire bulldozer starts moving."""
import json
from pathlib import Path


def generate():
    rows = []
    for mode, suffix in (('worker_report', 'WorkerReport'),
                         ('organizer_direct', 'OrganizerDirect')):
        name = f'FiveCiviliansAt80_75AfterOriginalFireDozerMovesThenFireAt80_80_{suffix}'
        preset = {
            'name': name,
            'description': ('Contain the original fire and rescue five initial civilians. '
                            'After the original-fire bulldozer has started physical work, '
                            'respond to five more civilians near (80,75) and a later fire '
                            'near (80,80). Continue unfinished original work.'),
            'game_type': 5, 'map_size': 100, 'max_steps': 100,
            'fire_spread_frequency': 500, 'civilian_count': 5,
            'civilian_clusters': 1, 'civilian_move_frequency': 800,
            'known': False, 'water': True, 'vegetation_density_offset': 30,
            'starting_firefighter_agents': 8, 'starting_drone_agents': 1,
            'starting_helicopter_agents': 1, 'starting_bulldozer_agents': 1,
            'scheduled_events': [
                {'event_id': 'five_civilians_at_80_75', 'timestep': 8,
                 'latest_timestep': 18,
                 'release_condition': 'original_fire_dozer_moved_and_initial_rescue_unfinished',
                 'action': 'spawn_civilians_5', 'x': 80, 'y': 75,
                 'announcement': 'Five more civilians reported near (80,75). Assess safe rescue and unfinished original work.'},
                {'event_id': 'fire_at_80_80', 'timestep': 14,
                 'after_event_id': 'five_civilians_at_80_75', 'delay_steps': 6,
                 'action': 'start_fire', 'x': 80, 'y': 80,
                 'announcement': 'A new fire reported near (80,80), five cells from the new civilian report. Reassess rescue access and fire control.'},
            ],
        }
        rows.append({'id': name, 'preset': preset, 'design': {
            'information_mode': mode,
            'release_contract': 'new civilians at first step >=8 with a moved original-fire bulldozer, active fire, fewer than five initial civilians rescued; if absent at step 18, release is labelled fallback and excluded from commitment-conditioned analysis',
            'second_event': 'new fire six decision steps after civilian event submission',
            'status': 'state-triggered candidate; physical event effect and rescue outcome need verification',
        }})
    return rows


if __name__ == '__main__':
    path = Path(__file__).with_name('tasks.json')
    rows = generate()
    path.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + '\n')
    print(f'{len(rows)} conditional tasks -> {path}')
