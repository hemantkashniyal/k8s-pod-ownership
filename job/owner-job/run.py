from typing import Union, Literal
from dotenv import load_dotenv
import logging
import os
from datetime import datetime
import redis
from kubernetes import client, config, watch

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


def get_redis():
    logger.info(f"creating redis client")
    redis_client = redis.Redis(host=database_host, port=database_port, db=database_db)
    return redis_client


def get_key(namespace: str, pod_name: str):
    return f"ownership/{namespace}/{pod_name}"


def get_ownership_key(key: Union[str, bytes]):
    ownership_key = key
    if isinstance(key, bytes):
        ownership_key = key.decode("utf-8")
    return "/".join(ownership_key.split("/")[1:])


def process_pod(event, redis_client, update_timestamp):
    pod = event["object"]
    namespace = pod.metadata.namespace
    pod_name = pod.metadata.name
    owner_references = pod.metadata.owner_references

    key = get_key(namespace, pod_name)
    data = {
        "namespace": namespace,
        "pod_name": pod_name,
        "owner": owner_references[0].kind if owner_references else "None",
        "owner_name": owner_references[0].name if owner_references else "None",
        "updated_at": f"{update_timestamp}",
        "deleted": "true" if event["type"] == "DELETED" else "false",
    }

    try:
        redis_client.hmset(key, data)
        if data["deleted"] == "true":
            redis_client.expire(key, deleted_ttl_sec)
        else:
            redis_client.persist(key)
        logger.info(f"Processed pod: {namespace}/{pod_name}")
    except Exception as e:
        logger.error(f"Error processing pod {namespace}/{pod_name}: {e}")


def mark_stale_pods(redis_client, updated_timestamp):
    keys = redis_client.keys("ownership/*")
    for key in keys:
        updated_at = redis_client.hget(key, "updated_at")
        if updated_at.decode("utf-8") != f"{updated_timestamp}":
            redis_client.hset(key, "deleted", "true")
            logger.info(f"Marking stale pod: {get_ownership_key(key)}")
            redis_client.expire(key, deleted_ttl_sec)


def process_pods(redis_client, current_timestamp):
    v1 = client.CoreV1Api()
    pods = v1.list_pod_for_all_namespaces().items
    for pod in pods:
        event = {"type": "ADDED", "object": pod}
        process_pod(event, redis_client, current_timestamp)


def main():
    logger.info(f"reading config")
    if environment == "dev":
        config.load_kube_config()
    else:
        config.load_incluster_config()

    logger.info("starting owner operator")

    redis_client = get_redis()
    current_timestamp = datetime.now().timestamp()

    try:
        process_pods(redis_client, current_timestamp)
        mark_stale_pods(redis_client, current_timestamp)
    except Exception as e:
        logger.error(f"Error in main loop: {e}")
    finally:
        redis_client.close()


if __name__ == "__main__":
    main()
