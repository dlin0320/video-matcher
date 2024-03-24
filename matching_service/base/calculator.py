from abc import ABC, abstractmethod
from logging import Logger
from typing import Dict

class BaseCalculator(ABC):
  _logger: Logger

  @abstractmethod
  def calculate_similarity(self, *args, **kwargs) -> Dict[int, float]:
    pass

  @abstractmethod
  def sum_sequence(self, *args, **kwargs) -> Dict[int, float]:
    pass