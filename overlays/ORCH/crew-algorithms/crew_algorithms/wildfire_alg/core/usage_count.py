"""Keep model usage totals correct when independent same-step calls run concurrently."""
from threading import Lock

_lock = Lock()


def record_usage(global_data, response=None):
    with _lock:
        global_data['api_calls'] += 1
        if response is not None:
            global_data['input_tokens'] += response.usage.prompt_tokens
            global_data['output_tokens'] += response.usage.completion_tokens
