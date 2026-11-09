"""Candidate compound missions where new fires threaten a newly reported rescue area."""
import json
from pathlib import Path

SEQUENCES = {
    'FiveCiviliansAt80_75ThenFireAt80_80': [
        (8, 'spawn_civilians_5', 80, 75), (14, 'start_fire', 80, 80)],
    'FireAt80_80ThenFiveCiviliansAt80_75': [
        (8, 'start_fire', 80, 80), (14, 'spawn_civilians_5', 80, 75)],
    'FiveCiviliansAt80_75ThenFiresAt80_80And80_20': [
        (8, 'spawn_civilians_5', 80, 75),
        (14, 'start_fire', 80, 80), (22, 'start_fire', 80, 20)],
}
CAPACITIES = ((1, 1, 'OneDozerOneHelicopter'),
              (2, 1, 'TwoDozersOneHelicopter'),
              (1, 2, 'OneDozerTwoHelicopters'),
              (2, 2, 'TwoDozersTwoHelicopters'))
MODES = (('worker_report', 'WorkerReport'),
         ('organizer_direct', 'OrganizerDirect'))


def generate():
    rows = []
    for sequence, events in SEQUENCES.items():
        for dozers, helicopters, capacity_name in CAPACITIES:
            for mode, mode_name in MODES:
                name = f'{sequence}_{capacity_name}_{mode_name}'
                announcements = []
                for step, action, x, y in events:
                    count = 'Five civilians' if action == 'spawn_civilians_5' else 'A fire'
                    report = f'{count} reported near ({x},{y}).'
                    if action == 'start_fire' and (x, y) == (80, 80):
                        report += (' This is close to the new rescue area. Check fire spread, '
                                   'clear threatening trees if useful, and coordinate transport of firefighters.')
                    elif action == 'spawn_civilians_5' and (x, y) == (80, 75):
                        report += (' This is close to the new fire area. Check safe access and '
                                   'coordinate firefighter transport and tree clearing if useful.')
                    announcements.append({'timestep': step, 'action': action,
                                          'x': x, 'y': y, 'announcement': report})
                preset = {
                    'name': name,
                    'description': ('Contain the original and newly reported fires; rescue the initial '
                                    'five civilians and any new civilians. Where a new fire threatens '
                                    'the rescue area, coordinate scouts, firefighters, the helicopter '
                                    'and the bulldozer if trees obstruct a safe approach.'),
                    'game_type': 5, 'map_size': 100, 'max_steps': 100,
                    'fire_spread_frequency': 500, 'civilian_count': 5,
                    'civilian_clusters': 1, 'civilian_move_frequency': 800,
                    'known': False, 'water': True, 'vegetation_density_offset': 30,
                    'starting_firefighter_agents': 8, 'starting_drone_agents': 1,
                    'starting_helicopter_agents': helicopters,
                    'starting_bulldozer_agents': dozers,
                    'scheduled_events': announcements,
                }
                rows.append({'id': name, 'preset': preset, 'design': {
                    'event_sequence': sequence, 'information_mode': mode,
                    'group_sources': {
                        'original_fire': 'bulldozer and firefighters',
                        'support': 'helicopter and firefighters',
                        'recon': 'drone and firefighter leader'},
                    'capacity': {'bulldozers': dozers, 'helicopters': helicopters, 'drones': 1},
                    'candidate_joint_work': [
                        'scout reports current fire and civilian positions',
                        'firefighters rescue the newly reported civilians',
                        'helicopter deploys firefighters when ground travel is too slow',
                        'bulldozer cuts a useful tree line only where observed trees threaten the approach'],
                    'status': 'candidate; event effect, overlap, useful trees, deadlines, and group-change benefit unverified',
                    'native_score_limit': 'Full_Game success checks fire extinction, not civilian rescue or cross-group handoff',
                }})
    return rows


if __name__ == '__main__':
    path = Path(__file__).with_name('tasks.json')
    rows = generate()
    path.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n')
    print(f'{len(rows)} candidate tasks -> {path}')
