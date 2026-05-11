import time

def retry_with_backoff(func, max_retries=3, base_delay=0.1):
    last_error = None
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            last_error = e
            delay = base_delay * (2 ** attempt)
            time.sleep(delay)
    raise last_error
