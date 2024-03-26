from database_service.redis.provider import RedisProvider
from common.producer_wrapper import ProducerWrapper
from message.frame import Frame
import numpy as np
import logging
import dotenv
import random
import time
import os

dotenv.load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

config = {
  'bootstrap.servers': 'kafka-cluster:9092',
  'security.protocol': 'SASL_PLAINTEXT',
  'sasl.mechanism': 'PLAIN',
  'sasl.username': 'user1',
  'sasl.password': os.environ.get('KAFKA_PASSWORD'),
  'log_level': 7,
  'log.queue': True
}

class MockProducer(ProducerWrapper):
  def __init__(self) -> None:
    self._logger = logging.getLogger(__name__)
    self._producer_config = config
    super().__init__()

  def start(self):
    self._logger.info('Producer started')
    redis = RedisProvider()
    sequence_counter = 0
    sequence_length = random.randint(1, 10)
    sequence_gap = 0

    for i in range(86400):
      if sequence_counter < sequence_length:
        data = self._create_array()
        sequence_counter += 1
        sequence_gap = 0
      else:
        sequence_gap += 1
        if random.random() < sequence_gap / 1000:
          sequence_length = random.randint(1, 10)
          data = self._create_array()
          sequence_counter = 1
        else:
          data = np.random.randint(2, size=(1024))
          sequence_counter = 0
      redis.set('channel1', Frame(timestamp=i, bits=data.tolist()))

    sequence_counter = 0
    sequence_length = random.randint(1, 10)
    sequence_gap = 0
    i = 86400

    while True:
      i += 1
      if sequence_counter < sequence_length:
        data = self._create_array()
        sequence_counter += 1
        sequence_gap = 0
      else:
        sequence_gap += 1
        if random.random() < sequence_gap / 100:
          sequence_length = random.randint(1, 10)
          data = self._create_array()
          sequence_counter = 1
        else:
          data = np.random.randint(2, size=(1024))
          sequence_counter = 0

      self.produce(['channel1'], {'timestamp': i, 'bits': data.tolist()})
      time.sleep(1)
      
  def _create_array(self):
    first_part = np.ones(256, dtype=int)
    second_part = np.random.randint(2, size=768)
    arr = np.concatenate((first_part, second_part))
    return arr
  
if __name__ == '__main__':
  MockProducer().start()