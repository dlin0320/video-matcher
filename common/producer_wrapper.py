from common.logger import kafka_logger
from confluent_kafka import Producer
from logging import Logger
from typing import Dict
import json

class ProducerWrapper():
  _logger: Logger
  _producer_config: Dict

  def __init__(self) -> None:
    try:
      self._producer = Producer(**self._producer_config, error_cb=lambda err: kafka_logger.error(err))
      self._logger.info('Producer init success')
    except Exception as e:
      self._logger.error(f'Producer init failed: {e}')

  def _delivery_report(self, err, data):
    if err:
      self._logger.error(f'Message delivery failed: {err}')
    else:
      self._logger.info(f'Message delivered to {data.topic()} [{data.partition()}] @ {data.offset()}')

  def produce(self, topics, data):
    try:
      for topic in topics:
        self._producer.produce(topic, value=json.dumps(data), callback=self._delivery_report)
        self._producer.poll(0)
      self._producer.flush()
    except Exception as e:
      self._logger.info(f'Error in producer: {e}')
    finally:
      self._producer.flush()