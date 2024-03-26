from abc import ABC, abstractmethod
from logging import Logger
from typing import Dict

class BaseCalculator(ABC):
  _logger: Logger

  @classmethod
  @abstractmethod
  def calculate_similarity(cls, target_bits, processed_data) -> Dict[int, float]:
    pass

  @classmethod
  @abstractmethod
  def sum_sequence(cls, scores) -> Dict[int, float]:
    pass

  @classmethod
  def get_scores(cls, topic, timestamp, data) -> Dict[int, float]:
    scores = cls.calculate_similarity(*data)
    cls._logger.info(f'Similarity calculated for {topic}:{timestamp}')
    sums = cls.sum_sequence(scores)
    cls._logger.info(f'Sequence summed for {topic}:{timestamp}')
    return sums