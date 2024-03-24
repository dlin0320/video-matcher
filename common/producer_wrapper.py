from common.logger import kafka_logger
from confluent_kafka import Producer
from logging import Logger
import json

config = {
  'bootstrap.servers': 'my-kafka.default.svc.cluster.local:9092',
  'security.protocol': 'SASL_PLAINTEXT',
  'sasl.mechanism': 'PLAIN',
  'sasl.username': 'user1',
  'sasl.password': 'vdjTOYdTvQ',
  'log_level': 7,
  'log.queue': True
}

class ProducerWrapper():
  _logger: Logger

  def __init__(self) -> None:
    try:
      self._producer = Producer(**config, error_cb=lambda err: kafka_logger.error(err))
      self._logger.info('ProducerWrapper init success')
    except Exception as e:
      self._logger.error(f'Producer init failed: {e}')

  def _delivery_report(self, err, data):
    if err:
      self._logger.error(f'Message delivery failed: {err}')

  def produce(self, topics, data):
    try:
      for topic in topics:
        self._producer.produce(topic, value=json.dumps(data), callback=self._delivery_report)
        self._producer.poll(0)
      self._producer.flush()
    except Exception as e:
      self._logger.error(f'Error in producer: {e}')
    finally:
      self._producer.flush()