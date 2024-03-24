from typing import List, Dict
from common.decorator import timer
from matching_service.base.calculator import BaseCalculator
from common.logger import get_logger
from message.frame import Frame
import numpy as np

TOTAL_BITS = 1024

LEADING_BITS = 256

SEQUENCE_LENGTH = 5

class SyncopateCalculator(BaseCalculator):
  @property
  def config(self):
    return {
      'total_bits': self._total_bits,
      'leading_bits': self._leading_bits,
      'sequence_length': self._sequence_length
    }
  
  @config.setter
  def config(self, config: Dict):
    self._total_bits = config.get('total_bits', self._total_bits)
    self._leading_bits = config.get('leading_bits', self._leading_bits)
    self._sequence_length = config.get('sequence_length', self._sequence_length)

  def __init__(self):
    self._logger = get_logger(__name__)
    self._total_bits = TOTAL_BITS
    self._leading_bits = LEADING_BITS
    self._sequence_length = SEQUENCE_LENGTH

  @timer()
  def xor_transform(self, frames: List[Frame]):
    for i in range(len(frames)-1, 0, -1):
      yield {frames[i].timestamp: np.bitwise_xor(frames[i].bits, frames[i - 1].bits)}

  @timer()
  def calculate_similarity(self, target_bits: List[int], processed_data: Dict[int, List[int]] = {}):
    scores = {}

    if len(target_bits) != self._total_bits:
      self._logger.error(f"Invalid target bits length: {len(target_bits)}, {self._total_bits} expected")
      return scores

    for timestamp, previous_bits in processed_data.items():
      if len(previous_bits) != self._total_bits:
        self._logger.error(f"Invalid frame bits length: {len(previous_bits)}, {self._total_bits} expected")
        continue
      product = np.prod(1 - np.bitwise_xor(target_bits[:self._leading_bits], previous_bits[:self._leading_bits]))
      weights = (self._total_bits - np.arange(0, self._total_bits - self._leading_bits)) / self._total_bits
      summation = np.sum((1 - np.bitwise_xor(target_bits[self._leading_bits:], previous_bits[self._leading_bits:])) * weights)
      scores[timestamp] = product * summation

    return scores

  @timer()
  def sum_sequence(self, scores: Dict[int, float]):
    sums = {}
    for timestamp, score in scores.items():
      sum = score
      for offset in range(self._sequence_length):
        sum += scores.get(timestamp - offset, 0)
      sums[timestamp] = sum

    return sums