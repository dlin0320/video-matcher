from database_service.mock.provider import MockProvider
from matching_service.syncopate.calculator import SyncopateCalculator
from matching_service.syncopate.matcher import SyncopateMatcher
from fastapi.testclient import TestClient
from matching_service.api import app
from message.frame import Frame
import numpy as np
import unittest
import warnings

class TestCalculator(unittest.TestCase):
  @classmethod
  def setUpClass(cls) -> None:
    cls.calculator = SyncopateCalculator()
    bits = np.random.randint(2, size=(86400, 1024))
    cls.frames = [Frame(timestamp=i, bits=bits[i]) for i in range(86400)]  
    target_bits = np.random.randint(2, size=(1024))
    processed_data = {frame.timestamp: frame.bits for frame in cls.frames}
    cls.scores, execution_time = cls.calculator.calculate_similarity(target_bits, processed_data)
    if execution_time > 5:
      warnings.warn(f"Execution time: {execution_time} seconds")

  def test_xor_transform(self):
    result, execution_time = self.calculator.xor_transform(self.frames)

    if execution_time > 5:
      warnings.warn(f"Execution time: {execution_time} seconds")

    assert len(list(result)) == len(self.frames) - 1

  def test_calculate_similarity(self):
    assert len(self.scores) == len(self.frames)
    assert all(isinstance(timestamp, int) for timestamp in self.scores.keys())
    assert all(isinstance(score, float) for score in self.scores.values())

  def test_sum_sequence(self):
    sums, execution_time = self.calculator.sum_sequence(self.scores)

    if execution_time > 5:
      warnings.warn(f"Execution time: {execution_time} seconds")

    assert len(sums) == len(self.frames)
    assert all(isinstance(timestamp, int) for timestamp in self.scores.keys())
    assert all(isinstance(score, float) for score in sums.values())

class TestMatcher(unittest.TestCase):
  def setUp(self) -> None:
    self.matcher = SyncopateMatcher()
    self.matcher._provider = MockProvider()
    self.matcher.start()

  def tearDown(self) -> None:
    self.matcher.stop()

  def test_random(self):
    pass

class TestAPI(unittest.TestCase):
  def setUp(self) -> None:
    self.client = TestClient(app)
    self.matcher = SyncopateMatcher()
    self.calculator = SyncopateMatcher()._calculator
    self.matcher.start()

  def tearDown(self) -> None:
    SyncopateMatcher().stop()

  def test_config(self):
    response = self.client.get("/syncopate/config")
    self.assertEqual(response.status_code, 200)
    assert response.json() == {
      'matching_window': SyncopateMatcher().config['matching_window'],
      'matching_threshold': SyncopateMatcher().config['matching_threshold']
    }

    response = self.client.post("/syncopate/config", 
      json={'matching_window': 100, 'matching_threshold': 200})
    self.assertEqual(response.status_code, 200)
    assert SyncopateMatcher().config['matching_window'] == 100
    assert SyncopateMatcher().config['matching_threshold'] == 200

  def test_calculator_config(self):
    response = self.client.get("/syncopate/calculator/config")
    self.assertEqual(response.status_code, 200)
    assert response.json() == {
      'total_bits': self.calculator.config['total_bits'],
      'leading_bits': self.calculator.config['leading_bits'],
      'sequence_length': self.calculator.config['sequence_length']
    }

    response = self.client.post("/syncopate/calculator/config", 
      json={'total_bits': 100, 'leading_bits': 200, 'sequence_length': 300})
    self.assertEqual(response.status_code, 200)
    assert self.calculator.config['total_bits'] == 100
    assert self.calculator.config['leading_bits'] == 200
    assert self.calculator.config['sequence_length'] == 300

  def test_topics(self):
    response = self.client.get("/syncopate/topics")
    self.assertEqual(response.status_code, 200)
    assert response.json() == list(SyncopateMatcher().topics)

    response = self.client.post("/syncopate/topics/subscribe", json={'topics': ['t1', 't2']})
    self.assertEqual(response.status_code, 200)
    assert SyncopateMatcher().topics == {'t1', 't2'}

    response = self.client.post("/syncopate/topics/unsubscribe", json={'topics': ['t1']})
    self.assertEqual(response.status_code, 200)
    assert SyncopateMatcher().topics == {'t2'}

    response = self.client.post("/syncopate/topics/update", json={'topics': ['t3', 't9']})
    self.assertEqual(response.status_code, 200)
    assert SyncopateMatcher().topics == {'t3', 't9'}

if __name__ == '__main__':
  unittest.main()