from confluent_kafka import Consumer, KafkaException
from common.logger import kafka_logger
from logging import Logger
from typing import Set
import json

config = {
  'bootstrap.servers': 'my-kafka.default.svc.cluster.local:9092', 
  'security.protocol': 'SASL_PLAINTEXT', 
  'sasl.mechanism': 'PLAIN', 
  'sasl.username': 'user1', 
  'sasl.password': 'vdjTOYdTvQ', 
  'group.id': 'my-group', 
  'auto.offset.reset': 'earliest',
  'log_level': 7,
  'log.queue': True
}

class ConsumerWrapper():
  _logger: Logger
  _topics: Set[str] = set([])

  @property
  def topics(self):
    return self._topics
  
  @topics.setter
  def topics(self, topics: Set[str]):
    try:
      self._consumer.subscribe(list(topics))
      self._topics = topics
    except Exception as e:
      self._logger.error(f'Error in subscribing to topics: {e}')

  def __init__(self):
    try:
      self._consumer = Consumer(**config, error_cb=lambda err: kafka_logger.error(err))
      self._logger.info('Consumer init success')
    except Exception as e:
      self._logger.error(f'Consumer init failed: {e}')

  def poll(self):
    try:
      msg = self._consumer.poll(1)
      if msg.error().code() == KafkaException._PARTITION_EOF:
        self._logger.warning(f'Consumer reached end of {msg.topic()} [{msg.partition()}] offset {msg.offset()}')
      elif msg.error():
        self._logger.error(f'Msg error: {msg.error()}')
      topic, value = str(msg.topic()), json.loads(msg.value())
    except AttributeError:
      topic, value = None, None
    except Exception as e:
      topic, value = None, None
      self._logger.error(f'Poll error: {e}')
    finally:
      return topic, value