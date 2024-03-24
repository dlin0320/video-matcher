from abc import ABC, abstractmethod
from message.frame import Frame

class BaseProvider(ABC):
  @abstractmethod
  def get(self, topic: str, timestamps: int):
    pass

  @abstractmethod
  def set(self, topic: str, frame: Frame):
    pass

  @abstractmethod
  def get_data_within_window(self, topic: str, matching_window: int):
    pass