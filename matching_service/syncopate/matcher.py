from common.logger import get_logger, debug_logger
from common.producer_wrapper import ProducerWrapper
from database_service.redis.provider import RedisProvider
from matching_service.base.matcher import BaseMatcher
from matching_service.syncopate.calculator import SyncopateCalculator
from common.decorator import singleton
from message.frame import Frame
from message.report import Report
from typing import List, Set, Dict, Type
import numpy as np
import os

MATCHING_WINDOW = 86400

MATCHING_THRESHOLD = 1000

MATCHING_COUNT = 10

consumer_config = {
  'bootstrap.servers': 'kafka-cluster:9092',
  'security.protocol': 'SASL_PLAINTEXT',
  'sasl.mechanism': 'PLAIN',
  'sasl.username': 'user1',
  'sasl.password': os.environ.get('KAFKA_PASSWORD'), 
  'group.id': 'matcher', 
  'auto.offset.reset': 'latest',
  'log_level': 7,
  'log.queue': True
}

producer_config = {
  'bootstrap.servers': 'kafka-cluster:9092',
  'security.protocol': 'SASL_PLAINTEXT',
  'sasl.mechanism': 'PLAIN',
  'sasl.username': 'user1',
  'sasl.password': os.environ.get('KAFKA_PASSWORD'),
  'log_level': 7,
  'log.queue': True
}

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
    def set(cls, topic: str, timestamp: int, bits: List[int]):
      if topic not in cls._store:
        cls._store[topic] = {}
      cls._store[topic][timestamp] = bits
      debug_logger.info(f'Storing data for {topic}:{timestamp}')

    @classmethod
    def get_range(cls, topic: str, start: int, end: int):
      channel = cls._store.get(topic, None)
      debug_logger.info(f'Getting data for {topic} from {start} to {end}')

      if channel and start <= end:
        return {timestamp: channel.get(timestamp, []) for timestamp in range(start, end+1)}
      return {}

    @classmethod
    def remove(cls, topic: str):
      cls._store.pop(topic, None)

  @property
  def config(self):
    return {
      'matching_window': self._matching_window,
      'matching_threshold': self._matching_threshold,
      'matching_count': self._matching_count
    }
  
  @config.setter
  def config(self, config: Dict):
    self._matching_window = config.get('matching_window', self._matching_window)
    self._matching_threshold = config.get('matching_threshold', self._matching_threshold)
    self._matching_count = config.get('matching_count', self._matching_count)
  
  def __init__(self, provider=None):
    self._logger = get_logger(__name__)
    self._producer_config = producer_config
    self._consumer_config = consumer_config

    ProducerWrapper.__init__(self)

    self._matching_window = MATCHING_WINDOW
    self._matching_threshold = MATCHING_THRESHOLD
    self._matching_count = MATCHING_COUNT
    self._provider: RedisProvider = provider or RedisProvider()
    self._calculator: Type[SyncopateCalculator] = SyncopateCalculator

    BaseMatcher.__init__(self)

    self.match_for(set(['channel1']))

  def _get_data(self, topic: str, frame: Frame):
    target_bits = frame.bits
    previous_bits = self._provider.get(topic, frame.timestamp-1)

    if previous_bits:
      target_bits = np.bitwise_xor(target_bits, previous_bits).tolist()
      self.ProcessedData.set(topic, frame.timestamp, target_bits)
    processed_data = self.ProcessedData.get_range(topic, frame.timestamp - self._matching_window, frame.timestamp)

    return target_bits, processed_data

  def _produce_report(self, topic, timestamp, threshold, sums: Dict[int, float]):
    matching_times = []
    sums.pop(timestamp, None)
    sorted_sums = sorted(sums.items(), key=lambda x: x[1], reverse=True)

    for _timestamp, sum in sorted_sums:
      if len(matching_times) > self._matching_count:
        break
      if sum >= threshold:
        matching_times.append(_timestamp)

    if matching_times:
      self.produce(['report'], Report(channel=topic, time=timestamp, matching_times=matching_times).model_dump())

  def match_for(self, topics: Set[str]):
    for topic in topics:
      raw_frames = self._provider.get_data_within_window(topic, self._matching_window)
      processed_frames = self._calculator.xor_transform(raw_frames)
      if processed_frames is None:
        continue
      debug_logger.info(list(processed_frames))
      for timestamp, bits in processed_frames:
        debug_logger.info(f'Processing frame: {topic}:{timestamp}')
        self.ProcessedData.set(topic, timestamp, bits)

    self.topics = topics

  def config_calculator(self, config: Dict=None):
    if config:
      if config.get('total_bits', self._calculator._total_bits) < config.get('leading_bits', self._calculator._leading_bits):
        raise ValueError('total_bits must be greater than leading_bits')
      self._calculator._total_bits = config.get('total_bits', self._calculator._total_bits)
      self._calculator._leading_bits = config.get('leading_bits', self._calculator._leading_bits)
      self._calculator._sequence_length = config.get('sequence_length', self._calculator._sequence_length)
    return {
      'total_bits': self._calculator._total_bits,
      'leading_bits': self._calculator._leading_bits,
      'sequence_length': self._calculator._sequence_length
    }