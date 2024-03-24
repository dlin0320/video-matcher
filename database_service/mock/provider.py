from database_service.base.provider import BaseProvider
from common.decorator import singleton
from message.frame import Frame
import numpy as np

@singleton
class MockProvider(BaseProvider):
  def __init__(self):
    bits = np.random.randint(2, size=(86400, 1024))
    self._frames = {i: bits[i] for i in range(86400)}
    for i in range(10):
      self.set(i, self._create_array())

    self.set("86399", self._create_array())

  def get(self, key):
    return self._frames.get(key)
  
  def set(self, key, value):
    self._frames[key] = value

  def get_data_within_window(self, topic: str, matching_window: int):
    return [Frame(timestamp=key, bits=value) for key, value in self._frames.items()]

  def _create_array(self):
    first_part = np.ones(256, dtype=int)
    second_part = np.random.randint(2, size=768)
    arr = np.concatenate((first_part, second_part))
    return arr