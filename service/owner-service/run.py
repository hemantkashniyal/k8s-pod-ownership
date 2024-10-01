from typing import Union, Literal

from dotenv import load_dotenv

import logging
import random
import uuid
import os
import redis
from fastapi import FastAPI, Depends, HTTPException

load_dotenv()

environment: Literal["dev", "prod"] = os.getenv("ENVIRONMENT", "dev")
database_host = os.getenv("DATABASE_HOST", "localhost")
database_port = os.getenv("DATABASE_PORT", "6379")
database_db = os.getenv("DATABASE_DB", "0")
deleted_ttl_sec = os.getenv("DELETED_TTL_SEC", "10")


logging.basicConfig(
    level=logging.INFO,  # Set the logging level
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("uvicorn")

app = FastAPI()


async def get_redis():
    redis_client = redis.Redis(host=database_host, port=database_port, db=database_db)
    try:
        yield redis_client
    finally:
        redis_client.close()


def get_key(namespace: str, pod_name: str):
    return f"ownership/{namespace}/{pod_name}"


def get_ownership_key(key: Union[str, bytes]):
    ownership_key = key
    if isinstance(key, bytes):
        ownership_key = key.decode("utf-8")
    return "/".join(ownership_key.split("/")[1:])


@app.get("/")
async def read_root(redis=Depends(get_redis)):
    try:
        pong = redis.ping()
    except Exception as e:
        logger.error(f"unable to ping redis: {e}")
        pong = str(e)

    app_status = "ok" if pong is True else "error"
    storage_status = "ok" if pong is True else "error"
    return {
        "app": app_status,
        "storage": storage_status,
    }


@app.get("/ownership/{namespace}/{pod_name}")
async def get_ownwership(namespace: str, pod_name: str, redis=Depends(get_redis)):
    try:
        data = redis.hgetall(get_key(namespace, pod_name))
        if not data:
            raise HTTPException(
                status_code=404,
                detail=f"pod not found: {namespace}/{pod_name}",
            )
        decoded_data = {k.decode("utf-8"): v.decode("utf-8") for k, v in data.items()}
        return decoded_data
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"unable to get ownership for {namespace}/{pod_name}: {e}")
        raise HTTPException(status_code=500, detail="")


if environment == "dev":

    @app.post("/ownership/{namespace}/{pod_name}")
    async def get_ownwership(namespace: str, pod_name: str, redis=Depends(get_redis)):
        random_id = str(uuid.uuid4())
        data = {
            "namespace": namespace,
            "pod_name": pod_name,
            "owner": f"owner-operator-{random_id}",
            "owner_name": f"owner-operator-name-{random_id}",
            "deleted": "true" if random.randint(0, 1) else "false",
        }
        try:
            key = get_key(namespace, pod_name)
            redis.hmset(key, data)
            if data["deleted"] == "true":
                redis.expire(key, deleted_ttl_sec)
            else:
                redis.persist(key)

            return {
                "status": "added ownership record",
                "data": data,
            }
        except Exception as e:
            logger.error(f"unable to set ownership for {namespace}/{pod_name}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/ownership")
    async def get_ownwership(redis=Depends(get_redis)):
        try:
            keys = redis.keys("ownership/*")

            ownership = {}
            for key in keys:
                data = redis.hgetall(key)
                ownership[get_ownership_key(key)] = {
                    k.decode("utf-8"): v.decode("utf-8") for k, v in data.items()
                }

            return {
                "status": "fetched ownership records",
                "ownership": ownership,
            }
        except Exception as e:
            logger.error(f"unable to get ownership: {e}")
            raise HTTPException(status_code=500, detail=str(e))
