import os
import redis
import logging

DB_PATH = os.environ.get("DB_PATH", "index_data.duckdb")
FMP_API_KEY = "tfE0OX2xq2vWRUd4Wr9Gc3IXpx5w9Vqi"  


# Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
DB_PATH = os.getenv("DB_PATH", "index_data.duckdb")

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_redis_client():
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
