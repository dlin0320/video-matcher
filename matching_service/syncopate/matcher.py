from common.logger import get_logger
from common.producer_wrapper import ProducerWrapper
from database_service.redis.provider import RedisProvider
from matching_service.base.matcher import BaseMatcher
from matching_service.syncopate.calculator import SyncopateCalculator
from common.decorator import singleton
from message.frame import Frame
from message.report import Report
from typing import List, Set, Dict

MATCHING_WINDOW = 86400

MATCHING_THRESHOLD = 300

@singleton
class SyncopateMatcher(BaseMatcher, ProducerWrapper):
  class ProcessedData:
    _store: Dict[str, Dict[int, List[int]]] = {}

    @classmethod
    def get(cls, topic: str, timestamp: int):
      channel = cls._store.get(topic, None)
      if channel:
        return channel.get(timestamp, [])
    
    @classmethod
    def set(cls, topic: str, frame: Frame):
      if topic not in cls._store:
        cls._store[topic] = {}
      cls._store[topic][frame.timestamp] = frame.bits

    @classmethod
    def get_range(cls, topic: str, start: int, end: int):
      channel = cls._store.get(topic, None)
      if channel:
        return {channel.get(timestamp, []) for timestamp in range(start, end+1)}

    @classmethod
    def remove(cls, topic: str):
      cls._store.pop(topic, None)

  @property
  def config(self):
    return {
      'matching_window': self._matching_window,
      'matching_threshold': self._matching_threshold
    }
  
  @config.setter
  def config(self, config: Dict):
    self._matching_window = config.get('matching_window', self._matching_window)
    self._matching_threshold = config.get('matching_threshold', self._matching_threshold)
  
  def __init__(self):
    self._logger = get_logger(__name__)

    ProducerWrapper.__init__(self)

    self._matching_window = MATCHING_WINDOW
    self._matching_threshold = MATCHING_THRESHOLD
    self._provider: RedisProvider = RedisProvider()
    self._calculator: SyncopateCalculator = SyncopateCalculator()

    BaseMatcher.__init__(self)

    self.match_for(self.topics)

  def _get_data(self, topic: str, frame: Frame):
    target_bits = frame.bits
    previous_bits = self.ProcessedData.get(topic, frame.timestamp-1)

    if previous_bits:
      target_bits = self._calculator.xor_transform([frame.bits, previous_bits])
      self.ProcessedData.set(topic, Frame(frame.timestamp, target_bits))
    processed_data = self.ProcessedData.get_range(topic, frame.timestamp - self._matching_window, frame.timestamp)

    return target_bits, processed_data

  def _produce_report(self, topic, timestamp, sums: Dict[int, float]):
    matching_times = []

    for _timestamp, sum in sums.items():
      if sum >= self._matching_threshold:
        matching_times.append(_timestamp)

    self.produce(['report'], Report(topic, timestamp, matching_times))

  def match_for(self, topics: Set[str]):
    for topic in topics:
      raw_frames = self._provider.get_data_within_window(topic, self._matching_window)
      processed_frames, _ = self._calculator.xor_transform(raw_frames)
      for frame in processed_frames:
        self.ProcessedData.set(topic, frame)

    self.topics = topics

  def config_calculator(self, config: Dict=None):
    if config:
      self._calculator.config = config
    return self._calculator.config