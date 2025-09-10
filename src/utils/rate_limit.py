from collections import deque
from time import sleep, time


def rate_limit_decorator(max_calls, period):
    calls = deque()

    def decorator(func):
        def wrapper(*args, **kwargs):
            nonlocal calls
            current_time = time()

            # Remove calls that are outside the time window
            while calls and calls[0] < current_time - period:
                calls.popleft()

            if len(calls) < max_calls:
                calls.append(current_time)
                return func(*args, **kwargs)
            sleep_time = period - (current_time - calls[0])
            sleep(sleep_time)
            calls.append(time())
            return func(*args, **kwargs)

        return wrapper

    return decorator


@rate_limit_decorator(max_calls=5, period=60)
def fetch_data_from_api(url):
    # Function to fetch data from the API
    pass  # Replace with actual API call logic
