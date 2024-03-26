from database_service.mock.provider import MockProvider
from matching_service.syncopate.calculator import SyncopateCalculator
from matching_service.syncopate.matcher import SyncopateMatcher
from fastapi.testclient import TestClient
from matching_service.api import app
from message.frame import Frame
import numpy as np
import unittest

class TestCalculator(unittest.TestCase):
  @classmethod
  def setUpClass(cls) -> None:
    cls.calculator = SyncopateCalculator()
    bits = np.random.randint(2, size=(86400, 1024))
    cls.frames = [Frame(timestamp=i, bits=bits[i]) for i in range(86400)]  
    target_bits = np.random.randint(2, size=(1024))
    processed_data = {frame.timestamp: frame.bits for frame in cls.frames}
    cls.scores = cls.calculator.calculate_similarity(target_bits, processed_data)

  def test_xor_transform(self):
    result = self.calculator.xor_transform(self.frames)

    assert len(list(result)) == len(self.frames) - 1

  def test_calculate_similarity(self):
    assert len(self.scores) == len(self.frames)
    assert all(isinstance(timestamp, int) for timestamp in self.scores.keys())
    assert all(isinstance(score, float) for score in self.scores.values())

  def test_sum_sequence(self):
    sums = self.calculator.sum_sequence(self.scores)

    assert len(sums) == len(self.frames)
    assert all(isinstance(timestamp, int) for timestamp in self.scores.keys())
    assert all(isinstance(score, float) for score in sums.values())

class TestAPI(unittest.TestCase):
  def setUp(self) -> None:
    self.client = TestClient(app)
    self.matcher = SyncopateMatcher(MockProvider())

  def tearDown(self) -> None:
    self.matcher._calculator._total_bits = 1024
    self.matcher._calculator._leading_bits = 256
    self.matcher._calculator._sequence_length = 5

  def test_config(self):
    response = self.client.get("/syncopate/config")
    self.assertEqual(response.status_code, 200)
    assert response.json() == {
      'matching_window': self.matcher.config['matching_window'],
      'matching_threshold': self.matcher.config['matching_threshold'],
      'matching_count': self.matcher.config['matching_count']
    }

    response = self.client.post("/syncopate/config", 
      json={'matching_window': 100, 'matching_threshold': 200, 'matching_count': 30})
    self.assertEqual(response.status_code, 200)
    assert self.matcher.config['matching_window'] == 100
    assert self.matcher.config['matching_threshold'] == 200
    assert self.matcher.config['matching_count'] == 30

  def test_calculator_config(self):
    response = self.client.get("/syncopate/calculator/config")
    self.assertEqual(response.status_code, 200)
    assert response.json() == {
      'total_bits': self.matcher._calculator._total_bits,
      'leading_bits': self.matcher._calculator._leading_bits,
      'sequence_length': self.matcher._calculator._sequence_length
    }

    response = self.client.post("/syncopate/calculator/config", 
      json={'total_bits': 1000, 'leading_bits': 200, 'sequence_length': 30})
    self.assertEqual(response.status_code, 200)
    assert self.matcher._calculator._total_bits == 1000
    assert self.matcher._calculator._leading_bits == 200
    assert self.matcher._calculator._sequence_length == 30

  def test_topics(self):
    response = self.client.get("/syncopate/topics")
    self.assertEqual(response.status_code, 200)
    assert response.json() == list(self.matcher.topics)

    response = self.client.post("/syncopate/topics/subscribe", json={'topics': ['channel1', 'channel2']})
    self.assertEqual(response.status_code, 200)
    assert self.matcher.topics == {'channel1', 'channel2'}

    response = self.client.post("/syncopate/topics/unsubscribe", json={'topics': ['channel1']})
    self.assertEqual(response.status_code, 200)
    assert self.matcher.topics == {'channel2'}

    response = self.client.post("/syncopate/topics/update", json={'topics': ['channel3', 'channel9']})
    self.assertEqual(response.status_code, 200)
    assert self.matcher.topics == {'channel3', 'channel9'}

if __name__ == '__main__':
  unittest.main()