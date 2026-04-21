# ==================================================
# Time Test Decorator
# ==================================================
import time
from config.settings import ENABLE_TIME_TEST

def time_test(func):
    """Decorator to measure function execution time"""
    if not ENABLE_TIME_TEST:
        return func

    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"⏱ {func.__name__}: {end - start:.4f}s")
        return result
    return wrapper


# ==================================================
# End Of Time Test Decorator
# ==================================================