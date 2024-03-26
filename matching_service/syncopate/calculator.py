from typing import List, Dict
from common.decorator import timer
from matching_service.base.calculator import BaseCalculator
from common.logger import get_logger, debug_logger
from message.frame import Frame
import numpy as np

TOTAL_BITS = 1024

LEADING_BITS = 256

SEQUENCE_LENGTH = 5

class SyncopateCalculator(BaseCalculator):
  _logger = get_logger(__name__)
  _total_bits = TOTAL_BITS
  _leading_bits = LEADING_BITS
  _sequence_length = SEQUENCE_LENGTH

  @classmethod
  @timer()
  def xor_transform(cls, frames: List[Frame]):
    debug_logger.info(f"XOR transforming {len(frames)} frames")
    if len(frames) < 2:
      return None
    for i in range(len(frames)-1, 0, -1):
      yield {frames[i].timestamp: np.bitwise_xor(frames[i].bits, frames[i - 1].bits)}

  @classmethod
  @timer()
  def calculate_similarity(cls, target_bits: List[int], processed_data: Dict[int, List[int]] = {}):
    debug_logger.info(f"Calculating similarity for {len(processed_data)} frames")
    scores = {}

    if len(target_bits) != cls._total_bits:
      cls._logger.error(f"Invalid target bits length: {len(target_bits)}, {cls._total_bits} expected")
      return scores

    for timestamp, previous_bits in processed_data.items():
      if len(previous_bits) != cls._total_bits:
        cls._logger.error(f"Invalid frame bits length: {len(previous_bits)}, {cls._total_bits} expected")
        continue
      product = np.prod(1 - np.bitwise_xor(target_bits[:cls._leading_bits], previous_bits[:cls._leading_bits]))
      weights = (cls._total_bits - np.arange(0, cls._total_bits - cls._leading_bits)) / cls._total_bits
      summation = np.sum((1 - np.bitwise_xor(target_bits[cls._leading_bits:], previous_bits[cls._leading_bits:])) * weights)
      score = product * summation
      scores[timestamp] = score
    debug_logger.info(f"Calculated {len(scores)} scores")
    
    return scores

  @classmethod
  @timer()
  def sum_sequence(cls, scores: Dict[int, float]):
    debug_logger.info(f"Summing scores: ", scores)
    sums = {}
    for timestamp, score in scores.items():
      sum = score
      for offset in range(cls._sequence_length):
        sum += scores.get(timestamp - offset, 0)
      sums[timestamp] = sum
    
    sorted(sums.items(), key=lambda x: x[0], reverse=True)

    return sums