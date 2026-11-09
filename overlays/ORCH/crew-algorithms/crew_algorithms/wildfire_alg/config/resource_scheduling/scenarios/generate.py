"""Generate concrete Full_Game event sequences for the ORCH event runner."""
import json
from pathlib import Path

EVENTS = {
    'SecondFireAt80_80': [(8, 'start_fire', 80, 80)],
    'FiveCiviliansAt20_80': [(8, 'spawn_civilians_5', 20, 80)],
    'SecondFireThenFiveCivilians': [(8, 'start_fire', 80, 80),
                                    (12, 'spawn_civilians_5', 20, 80)],
    'FiveCiviliansThenSecondFire': [(8, 'spawn_civilians_5', 20, 80),
                                    (12, 'start_fire', 80, 80)],
    'FireAt80_80ThenFireAt20_80': [(8, 'start_fire', 80, 80),
                                   (16, 'start_fire', 20, 80)],
    'FiveCiviliansThenNearbyFire': [(8, 'spawn_civilians_5', 20, 80),
                                    (12, 'start_fire', 20, 70)],
    'OneCivilianAt80_20': [(8, 'spawn_civilian', 80, 20)],
    'LateFireAt80_80': [(16, 'start_fire', 80, 80)],
    'SecondFireThenOneCivilian': [(8, 'start_fire', 80, 80),
                                  (12, 'spawn_civilian', 20, 80)],
    'OneCivilianThenTwoFires': [(8, 'spawn_civilian', 80, 20),
                                (12, 'start_fire', 80, 80),
                                (20, 'start_fire', 20, 80)],
}
ACTION_TEXT = {
    'start_fire': 'A new fire was reported',
    'spawn_civilians_5': 'Five more civilians were reported',
    'spawn_civilian': 'One more civilian was reported',
}


def make_preset(name, drones, events):
    return {
        'name': name,
        'description': ('Contain the original fire and rescue the initial five civilians. '
                        'Respond to later fire or civilian reports while continuing unfinished work.'),
        'game_type': 5, 'map_size': 100, 'max_steps': 100,
        'fire_spread_frequency': 500, 'civilian_count': 5,
        'civilian_clusters': 1, 'civilian_move_frequency': 800,
        'known': False, 'water': True, 'vegetation_density_offset': 30,
        'starting_firefighter_agents': 8, 'starting_drone_agents': drones,
        'starting_helicopter_agents': 1, 'starting_bulldozer_agents': 1,
        'scheduled_events': [
            {'timestep': step, 'action': action, 'x': x, 'y': y,
             'announcement': f'{ACTION_TEXT[action]} at ({x},{y}). Continue and reprioritize active work.'}
            for step, action, x, y in events],
    }


def generate():
    rows = []
    for sequence, events in EVENTS.items():
        for drones, capacity in ((1, 'OneDrone'), (2, 'TwoDrones')):
            for mode, label in (('worker_report', 'WorkerReport'),
                                ('organizer_direct', 'OrganizerDirect')):
                name = f'{sequence}_{capacity}_{label}'
                rows.append({'id': name, 'preset': make_preset(name, drones, events),
                             'design': {
                                 'event_sequence': sequence,
                                 'information_mode': mode,
                                 'drone_count': drones,
                                 'initial_goals': ['contain original fire', 'rescue initial five civilians'],
                                 'later_goals': [
                                     f'{ACTION_TEXT[action].lower()} at ({x},{y})'
                                     for _, action, x, y in events],
                                 'status': 'ORCH_config_ready; Unity_event_and_task_outcome_not_yet_validated',
                                 'scoring_limit': 'native Full_Game success does not separately score initial/new civilians or each fire',
                             }})
    for drones, capacity in ((1, 'OneDrone'), (2, 'TwoDrones')):
        name = f'OriginalFireAndFiveCivilians_{capacity}'
        rows.append({'id': name, 'preset': make_preset(name, drones, []),
                     'design': {'event_sequence': 'NoLaterEvent',
                                'information_mode': 'none', 'drone_count': drones,
                                'initial_goals': ['contain original fire', 'rescue initial five civilians'],
                                'later_goals': [],
                                'status': 'ORCH_config_ready; task_outcome_not_yet_validated',
                                'scoring_limit': 'native Full_Game success does not separately score civilian rescue'}})
    return rows


if __name__ == '__main__':
    path = Path(__file__).with_name('tasks.json')
    path.write_text(json.dumps(generate(), indent=2, ensure_ascii=False) + '\n')
    print(f'{len(generate())} scenarios -> {path}')
