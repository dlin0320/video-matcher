from logging import Logger
from common.consumer_wrapper import ConsumerWrapper
from database_service.base.provider import BaseProvider
from matching_service.base.calculator import BaseCalculator
from abc import ABC, abstractmethod
from typing import Dict
import multiprocessing
import threading
import atexit
import signal
import sys
import os

from message.frame import Frame

class BaseMatcher(ABC, ConsumerWrapper):
  _logger: Logger
  _calculator: BaseCalculator
  _provider: BaseProvider
  _matching_window: int

  @property
  def is_running(self):
    if not hasattr(self, '_run_flag'):
      self._run_flag = False
    return self._run_flag

  def __init__(self) -> None:
    try:
      super().__init__()
      atexit.register(self.stop)
      signal.signal(signal.SIGINT, lambda sig, frame: [self.stop(), sys.exit(0)])
      self._logger.info('Matching service started successfully')
    except Exception as e:
      self._logger.error(f'Matching service init failed: {e}')

  def start(self):
    if self.is_running:
      return
    self._run_flag = True
    if not hasattr(self, '_pool') or self._pool is None:
      self._pool = multiprocessing.Pool(os.cpu_count())
    threading.Thread(target=self._start, daemon=True).start()
    
  def stop(self):
    self._run_flag = False
    if self._pool:
      self._pool.close()
      self._pool.join()
      self._pool = None

  def _start(self):
    while self._run_flag:
      try:
        topic, value = self.poll()
        if topic and value:
          self._pool.apply_async(self._find_matches, args=(topic, Frame(**value),))
      except Exception as e:
        self._logger.error(f'Error in processing: {e}')

  def _find_matches(self, topic: str, frame: Frame):
    try:
      if frame.timestamp is not None and frame.bits is not None:
        self._provider.set(topic, frame)
        scores = self._calculator.calculate_similarity(*self._get_data(topic, frame))
        sums = self._calculator.sum_sequence(scores)
        self._produce_report(topic, frame.timestamp, sums)
        return True
    except Exception as e:
      self._logger.error(f'Error in matching: {e}')
      return False
    
  @abstractmethod
  def _get_data(self, topic: str, frame: Frame):
    pass

  @abstractmethod
  def _produce_report(self, scores: Dict[str, float]):
    pass