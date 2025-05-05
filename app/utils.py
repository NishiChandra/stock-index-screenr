import os
import redis
import logging

# Configuration
DB_PATH = os.getenv("DB_PATH", "/app/app/data/index_data.duckdb")  # default fallback if not passed
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_redis_client():
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
