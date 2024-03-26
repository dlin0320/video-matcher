from common.logger import debug_logger
import functools
import time

def timer():
  def decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
      start_time = time.time()
      result = func(*args, **kwargs)
      end_time = time.time()
      execution_time = end_time - start_time
      debug_logger.info(f"Execution time: {execution_time} seconds")
      return result
    return wrapper
  return decorator

def singleton(cls):
	def get_instance(*args, **kwargs):
		if cls not in get_instance.instances:
			get_instance.instances[cls] = cls(*args, **kwargs)
		return get_instance.instances[cls]

	get_instance.instances = {}
	return get_instance