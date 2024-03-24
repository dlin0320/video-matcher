from database_service.base.provider import BaseProvider
from typing import List
import redis
import json

from message.frame import Frame

EXPIRATION_BUFFER = 600

class RedisProvider(BaseProvider):
  def __init__(self):
    self._client = redis.Redis(db=0)

  def get(self, topic: str, timestamp: int):
    value = self._client.get(f'{topic}:{timestamp}')
    return json.loads(value) if value else []

  def get_all(self, topic: str, timestamps: List[int]):
    keys = [f'{topic}:{timestamp}' for timestamp in timestamps]
    values = self._client.mget(keys)
    return [json.loads(value) if value else [] for value in values]

  def set(self, topic: str, timestamp: int, value: List[int], ex=86400):
    self._client.set(f'{topic}:{timestamp}', json.dumps(value), ex=ex+EXPIRATION_BUFFER)

  def latest_timestamp(self, topic: str):
    keys = [int(key) for key in self._client.keys(f'{topic}:*')]
    return max(keys) if keys else None

  def get_data_within_window(self, topic: str, matching_window: int):
    if (end := self.latest_timestamp(topic)) and end > matching_window:
      start = end - matching_window
      timestamps = list(range(start, end+1))
      values = self.get_all(topic, timestamps)
      return [Frame(timestamp, value) for timestamp, value in zip(timestamps, values)]
    return []