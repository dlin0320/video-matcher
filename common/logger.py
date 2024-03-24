from logging.handlers import RotatingFileHandler
import logging
import os

def get_logger(name):
  os.makedirs("logs", exist_ok=True)
  logger = logging.getLogger(name)
  logger.setLevel(logging.DEBUG)
  logger.propagate = False
  formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
  max_log_size = 10 * 1024 * 1024
  backup_count = 10
  handler = RotatingFileHandler(f"logs/{name}.log".format(name), maxBytes=max_log_size, backupCount=backup_count)
  handler.setLevel(logging.DEBUG)
  handler.setFormatter(formatter)
  logger.addHandler(handler)
  return logger

default_logger = get_logger("default")

kafka_logger = get_logger("kafka")