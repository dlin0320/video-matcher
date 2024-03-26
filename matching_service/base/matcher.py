from concurrent.futures import ThreadPoolExecutor
from common.consumer_wrapper import ConsumerWrapper
from database_service.base.provider import BaseProvider
from matching_service.base.calculator import BaseCalculator
from abc import ABC, abstractmethod
from message.frame import Frame
from common.logger import debug_logger
from typing import Dict, Type
from logging import Logger
import multiprocessing
import threading
import atexit
import signal
import queue
import sys
import os

class BaseMatcher(ABC, ConsumerWrapper):
  _logger: Logger
  _provider: BaseProvider
  _calculator: Type[BaseCalculator]
  _matching_window: int
  _matching_threshold: float

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

      self._queue = queue.PriorityQueue()
      self._executor = ThreadPoolExecutor(max_workers=os.cpu_count())
      self._semaphore = threading.Semaphore(os.cpu_count())
      self._logger.info('Matching service init success')

      threading.Thread(target=self._poll, daemon=True).start()
      self._logger.info('Polling started')
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
    if hasattr(self, '_pool') and self._pool:
      self._pool.close()
      self._pool.join()
      self._pool = None

  def _poll(self):
    while True:
      try:
        topic, value = self.poll(2)
        if topic and value:
          frame = Frame(**value)
          debug_logger.info(f'Frame received: {topic}:{frame.timestamp}')
          self._provider.set(topic, frame)
          self._queue.put((frame.timestamp, (topic, frame)))
      except Exception as e:
        self._logger.error(f'Error in polling: {e}')

  def _start(self):
    while self._run_flag:
      try:
        _, (topic, frame) = self._queue.get()
        self._semaphore.acquire()
        self._executor.submit(self._find_matches, topic, frame)
      except Exception as e:
        self._logger.error(f'Error in processing: {e}')

  def _find_matches(self, topic: str, frame: Frame):   
    debug_logger.info(f'Matching started for {topic}:{frame.timestamp}')
    
    if self._pool is None or frame.timestamp is None or frame.bits is None:
      return

    try:
      data = self._get_data(topic, frame)
      result = self._pool.apply_async(self._calculator.get_scores, args=[topic, frame.timestamp, data])
      try:
        self._produce_report(topic, frame.timestamp, self._matching_threshold, result.get())
        self._logger.info(f'Matching completed for {topic}:{frame.timestamp}')
      except multiprocessing.TimeoutError:
        self._logger.error('Timeout in matching process')
      except Exception as e:
        self._logger.error(f'Error in matching process: {e}')
    except Exception as e:
      debug_logger.debug(f'Error in matching: {e}')
    finally:
      self._semaphore.release()
    
  @abstractmethod
  def _get_data(self, topic: str, frame: Frame):
    pass

  @abstractmethod
  def _produce_report(self, scores: Dict[str, float]):
    pass