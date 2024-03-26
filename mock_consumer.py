from common.consumer_wrapper import ConsumerWrapper
import logging
import dotenv
import os

dotenv.load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

config = {
  'bootstrap.servers': 'kafka-cluster:9092',
  'security.protocol': 'SASL_PLAINTEXT',
  'sasl.mechanism': 'PLAIN',
  'sasl.username': 'user1',
  'sasl.password': os.environ.get('KAFKA_PASSWORD'), 
  'group.id': 'mock', 
  'auto.offset.reset': 'latest',
  'log_level': 7,
  'log.queue': True
}

class MockConsumer(ConsumerWrapper):
  def __init__(self) -> None:
    self._logger = logging.getLogger(__name__)
    self._consumer_config = config
    super().__init__()

  def start(self):
    self._logger.info('Consumer started')
    self.topics = set(['report'])
    while True:
      topic, value = self.poll(10)
      if topic and value:
        self._logger.info(f'Topic: {topic}, Value: {value}')

if __name__ == '__main__':
  MockConsumer().start()