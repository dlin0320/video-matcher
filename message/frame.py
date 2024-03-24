from pydantic import BaseModel
from typing import List, Optional

class Frame(BaseModel):
  timestamp: Optional[int] = None
  bits: Optional[List[int]] = None

  class Config:
    extra = 'ignore'