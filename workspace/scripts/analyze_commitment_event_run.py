"""Summarize event release, information routing, and observable handoffs.

This deliberately does not infer regional extinction or individual civilian rescue
from Full_Game's global rewards.
"""
import argparse
import json
from pathlib import Path
import re
import math


# Optimistic distances only. Trees can slow firefighters and bulldozers;
# interaction and communication consume additional decision steps.
MAX_TRAVEL_PER_STEP = {0: 12, 1: 8, 2: 20, 3: 30}
WORKER_NAMES = {0: 'firefighter', 1: 'bulldozer', 2: 'drone', 3: 'helicopter'}


def mentions_coordinate(content, x, y):
    return bool(re.search(rf'(?<!\d){x}\s*,\s*{y}(?!\d)', content or ''))


def first_step(events, kind, earliest, coordinate=None, message_type=None, sender=None):
    for item in events:
        if item['type'] != kind or item['step'] is None or item['step'] < earliest:
            continue
        payload = item['payload']
        if message_type and payload.get('message_type') != message_type:
            continue
        if sender is not None and payload.get('sender') != sender:
            continue
        if coordinate and not mentions_coordinate(payload.get('content', ''), *coordinate):
            continue
        return item['step']
    return None


def analyze(event_path):
    raw = [json.loads(line) for line in event_path.read_text().splitlines() if line.strip()]
    current_step = None
    events = []
    worker_types = {}
    initial_topology = None
    last_topology = None
    first_topology_change = None
    topology_changes = []
    for event in raw:
        kind, payload = event.get('event_type'), event.get('payload', {})
        if kind == 'TASK_WORLD_SNAPSHOT':
            current_step = payload.get('step')
            worker_types.update({aid: node.get('facts', {}).get('agent_type')
                                 for aid, node in payload.get('nodes', {}).items()})
        step = payload.get('step', current_step)
        events.append({'type': kind, 'step': step, 'payload': payload,
                       'agent_id': event.get('agent_id')})
        if kind == 'TASK_GRAPH_COMMITTED':
            topology = {edge['id']: (tuple(sorted(edge['members'])), edge['leader'])
                        for edge in payload.get('edges', [])}
            if initial_topology is None:
                initial_topology = topology
            elif topology != last_topology:
                topology_changes.append(step)
                if first_topology_change is None:
                    first_topology_change = step
            last_topology = topology
    releases = [item for item in events if item['type'] == 'TASK_EVENT_RELEASE_DECISION']
    report = {'event_path': str(event_path),
              'event_releases': [],
              'first_topology_change_step': first_topology_change,
              'source_view_civilian_sighting_steps': [item['step'] for item in events
                  if item['type'] == 'TASK_SOURCE_VIEW_CIVILIAN_SIGHTING'],
              'source_view_fire_sighting_steps': [item['step'] for item in events
                  if item['type'] == 'TASK_SOURCE_VIEW_FIRE_SIGHTING'],
              'new_civilian_entity_count': None,
              'new_civilians_rescued': None,
              'new_fire_region_extinguished': None,
              'physical_outcomes_note': 'Unity global rewards do not identify new civilian entities or a fire region'}
    coordinates = {'five_civilians_at_80_75': (80, 75), 'fire_at_80_80': (80, 80)}
    for release in releases:
        payload = release['payload']
        name = payload.get('event_id')
        coordinate = coordinates.get(name)
        step = release['step']
        snapshot = next((item['payload'] for item in reversed(events)
                         if item['type'] == 'TASK_WORLD_SNAPSHOT' and
                         item['step'] == step and
                         item['payload'].get('phase') == 'before_action'), None)
        travel = {}
        if snapshot and coordinate:
            for aid, node in snapshot.get('nodes', {}).items():
                kind = node.get('facts', {}).get('agent_type')
                if not node.get('online') or kind not in MAX_TRAVEL_PER_STEP:
                    continue
                position = node.get('position')
                if position is None:
                    continue
                distance = math.dist(position, coordinate)
                name_of_kind = WORKER_NAMES[kind]
                candidate = {'agent_id': aid, 'position': position,
                             'euclidean_distance': round(distance, 2),
                             'optimistic_travel_steps': math.ceil(distance / MAX_TRAVEL_PER_STEP[kind])}
                if name_of_kind not in travel or distance < travel[name_of_kind]['euclidean_distance']:
                    travel[name_of_kind] = candidate
        delivery = next((item for item in events
                         if item['type'] == 'TASK_WORKER_EVENT_REPORT_DELIVERED' and
                         item['payload'].get('event_timestep') == step and
                         item['payload'].get('event_action') == payload.get('action')), None)
        first_worker = delivery['step'] if delivery else None
        direct_notice = next((item for item in events
                              if item['type'] == 'TASK_ENVIRONMENT_NOTICE' and
                              item['payload'].get('event', {}).get('timestep') == step and
                              item['payload'].get('event', {}).get('action') == payload.get('action')), None)
        organizer_request_with_coordinate = next((item['step'] for item in events
            if item['type'] == 'TASK_ORGANIZER_REQUEST' and item['step'] is not None
            and item['step'] >= step and coordinate
            and mentions_coordinate(json.dumps(item['payload'].get('messages', []), ensure_ascii=False), *coordinate)), None)
        sighting_type = ('TASK_SOURCE_VIEW_FIRE_SIGHTING' if name == 'fire_at_80_80'
                         else 'TASK_SOURCE_VIEW_CIVILIAN_SIGHTING')
        sighting = next((item for item in events
                         if item['type'] == sighting_type and
                         item['payload'].get('event_timestep') == step and
                         item['payload'].get('event_coordinate') == list(map(float, coordinate))), None) if coordinate else None
        report_sender = delivery['payload'].get('recipient') if delivery else None
        first_report = first_step(events, 'TASK_MESSAGE_DELIVERED', step, coordinate,
                                  'REPORT', report_sender) if report_sender else None
        first_center = first_step(events, 'TASK_LEADER_REPORT', step, coordinate)
        first_plan = first_step(events, 'TASK_GRAPH_COMMITTED', step + 1)
        dozer_cut = next((item['step'] for item in events
                          if item['type'] == 'TASK_ACTION_AUTHORIZED' and
                          item['step'] is not None and item['step'] > step and
                          worker_types.get(item['agent_id']) == 1 and
                          (item['payload'].get('action') or [None])[0] == 1), None)
        helicopter_pickup = next((item['step'] for item in events
                                  if item['type'] == 'TASK_ACTION_AUTHORIZED' and
                                  item['step'] is not None and item['step'] > step and
                                  worker_types.get(item['agent_id']) == 3 and
                                  (item['payload'].get('action') or [None])[0] == 1), None)
        report['event_releases'].append({
            'event_id': name, 'step': step, 'release_reason': payload.get('release_reason'),
            'old_fire_dozer_moved': payload.get('original_fire_dozer_moved'),
            'closest_worker_by_type_at_release': travel,
            'first_worker_event_delivery_step': first_worker,
            'first_direct_organizer_notice_step': direct_notice['step'] if direct_notice else None,
            'first_organizer_request_with_event_coordinate_step': organizer_request_with_coordinate,
            'first_fresh_source_view_target_sighting_step': sighting['step'] if sighting else None,
            'fresh_source_view_target_sighting': sighting['payload'] if sighting else None,
            'first_worker_to_leader_report_with_event_coordinate_step': first_report,
            'first_leader_to_organizer_report_with_event_coordinate_step': first_center,
            'first_plan_commit_after_event_step': first_plan,
            'first_topology_change_after_event_step': next(
                (change for change in topology_changes if change is not None and change > step), None),
            'first_topology_change_after_organizer_report_step': next(
                (change for change in topology_changes if first_center is not None
                 and change is not None and change > first_center), None),
            'first_dozer_cut_command_after_event_step': dozer_cut,
            'first_helicopter_pickup_command_after_event_step': helicopter_pickup,
            'command_note': 'authorized commands are not verified physical effects; graph changes after an event or report are temporal associations, not causal proof'})
    validations = [item['payload'] for item in events if item['type'] == 'TASK_VALIDATED']
    if validations:
        report['last_validator'] = validations[-1]
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('events', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = analyze(args.events)
    output = args.output or args.events.with_name('commitment_event_analysis.json')
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(output)


if __name__ == '__main__':
    main()
