from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from common.logger import get_logger
from matching_service.syncopate.matcher import SyncopateMatcher
from typing import List, Optional

class MatcherConfig(BaseModel):
  matching_window: Optional[int] = Field(None, ge=1)
  matching_threshold: Optional[float] = Field(None, ge=1)
  matching_count: Optional[int] = Field(None, ge=1)

class CalculatorConfig(BaseModel):
  total_bits: Optional[int] = Field(None, ge=1)
  leading_bits: Optional[int] = Field(None, ge=1)
  sequence_length: Optional[int] = Field(None, ge=1)

class Topics(BaseModel):
  topics: List[str] = []

logger = get_logger(__name__)

app = FastAPI()

@app.exception_handler(Exception)
async def exception_handler(_, exc):
  logger.error(f'Error: {exc}')
  return HTTPException(status_code=500, detail=str(exc))

@app.post('/syncopate/start')
async def start():
  SyncopateMatcher().start()
  return {'status': 'started'}

@app.post('/syncopate/stop')
async def stop():
  SyncopateMatcher().stop()
  return {'status': 'stopped'}

@app.get('/syncopate/config')
async def get_config():
  return SyncopateMatcher().config

@app.post('/syncopate/config')
async def update_config(config: MatcherConfig):
  SyncopateMatcher().config = config.model_dump(exclude_defaults=True)
  return {'status': 'matcher configs updated'}

@app.get('/syncopate/calculator/config')
async def get_calculator_config():
  return SyncopateMatcher().config_calculator()

@app.post('/syncopate/calculator/config')
async def update_calculator_config(config: CalculatorConfig):
  SyncopateMatcher().config_calculator(config.model_dump(exclude_defaults=True))
  return {'status': 'calculator configs updated'}

@app.get('/syncopate/topics')
async def get_topics():
  return SyncopateMatcher().topics

@app.post('/syncopate/topics/subscribe')
async def subscribe_topics(args: Topics):
  new_topics = SyncopateMatcher().topics.union(args.topics)
  SyncopateMatcher().match_for(new_topics)
  return {'status': 'subscribed'}

@app.post('/syncopate/topics/unsubscribe')
async def unsubscribe_topics(args: Topics):
  new_topics = SyncopateMatcher().topics.difference(args.topics)
  SyncopateMatcher().match_for(new_topics)
  return {'status': 'unsubscribed'}

@app.post('/syncopate/topics/update')
async def update_topics(args: Topics):
  new_topics = set(args.topics)
  SyncopateMatcher().match_for(new_topics)
  return {'status': 'topics updated'}