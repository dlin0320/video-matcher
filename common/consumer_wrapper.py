from confluent_kafka import Consumer, KafkaException
from common.logger import kafka_logger
from logging import Logger
from typing import Set, Dict
import json

class ConsumerWrapper():
  _logger: Logger
  _topics: Set[str] = set([])
  _consumer_config: Dict

  @property
  def topics(self):
    return self._topics

  @topics.setter
  def topics(self, topics: Set[str]):
    try:
      if topics:
        self._consumer.subscribe(list(topics))
        self._topics = topics
        self._logger.info(f'Subscribed to topics: {topics}')
    except Exception as e:
      self._logger.error(f'Error in subscribing to topics: {self.topics}, {e}')

  def __init__(self):
    try:
      self._consumer = Consumer(**self._consumer_config, error_cb=lambda err: kafka_logger.error(err))
      self._logger.info('Consumer init success')
    except Exception as e:
      self._logger.error(f'Consumer init failed: {e}')

  def poll(self, timeout):
    try:
      msg = self._consumer.poll(timeout)
      if msg is None:
        return None, None
      elif msg.error():
        if msg.error().code() == KafkaException._PARTITION_EOF:
          self._logger.warning(f'Consumer reached end of {msg.topic()} [{msg.partition()}] offset {msg.offset()}')
        else:
          self._logger.error(f'Msg error: {msg.error()}')
      else:
        if msg.value():
          topic, value = str(msg.topic()), json.loads(msg.value())
        else:
          topic, value = str(msg.topic()), None
        return topic, value
    except Exception as e:
      self._logger.error(f'Poll error: {e}')
      return None, None