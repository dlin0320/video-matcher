from pydantic import BaseModel
from typing import List

class Report(BaseModel):
  channel: str
  time: int
  matching_times: List[int]

  class Config:
    extra = 'ignore'