"""Release scheduled Unity events after a recorded state condition or prior event."""


def event_for_step(events, step, submitted, condition_ready=None):
    """Return one copy with the actual submission step; never claim physical effect."""
    by_id = {event.get('event_id'): event for event in submitted if event.get('event_id')}
    for raw in events:
        event = dict(raw)
        event_id = event.get('event_id')
        if event_id and event_id in by_id:
            continue
        if event.get('after_event_id'):
            prior = by_id.get(event['after_event_id'])
            if prior is None or step < prior['timestep'] + event.get('delay_steps', 0):
                continue
            reason = 'after_previous_event'
        elif event.get('release_condition'):
            earliest = event.get('timestep', 0)
            latest = event.get('latest_timestep', earliest)
            if step < earliest:
                continue
            if condition_ready is not None and condition_ready(event):
                reason = 'condition_met'
            elif step >= latest:
                reason = 'fallback_latest_timestep'
            else:
                continue
        elif event.get('timestep') == step:
            reason = 'fixed_timestep'
        else:
            continue
        event['configured_timestep'] = event['timestep']
        event['timestep'] = step
        event['release_reason'] = reason
        return event
    return None
