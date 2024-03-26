from database_service.base.provider import BaseProvider
from message.frame import Frame
from typing import List
import redis
import ast
import os

EXPIRATION_BUFFER = 600

class RedisProvider(BaseProvider):
  def __init__(self):
    self._client = redis.Redis(host='my-redis', port=6379, db=0)

  def _safe_int(self, value):
    try:
      return int(value)
    except:
      return 0

  def get(self, topic: str, timestamp: int):
    value = self._client.get(f'{topic}:{timestamp}')
    return ast.literal_eval(value.decode()) if value else []

  def get_all(self, topic: str, timestamps: List[int]):
    keys = [f'{topic}:{timestamp}' for timestamp in timestamps]
    values = self._client.mget(keys)
    return [ast.literal_eval(value) if value else [] for value in values]

  def set(self, topic: str, frame: Frame, ex=86400):
    self._client.set(f'{topic}:{frame.timestamp}', str(frame.bits), ex=ex+EXPIRATION_BUFFER)

  def latest_timestamp(self, topic: str):
    keys = [self._safe_int(key) for key in self._client.keys(f'{topic}:*')]
    return max(keys) if keys else None

  def get_data_within_window(self, topic: str, matching_window: int):
    if (end := self.latest_timestamp(topic)) and end > matching_window:
      start = end - matching_window
      timestamps = list(range(start, end+1))
      values = self.get_all(topic, timestamps)
      return [Frame(timestamp=timestamp, bits=value) for timestamp, value in zip(timestamps, values)]
    return []