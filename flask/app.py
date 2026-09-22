"""Tiny Flask app used by the docker-examples.

Endpoints:
  GET /            -> HTML page showing a visit counter
  GET /health      -> {"status": "ok"} (does not touch redis, for liveness)
  GET /count       -> JSON counter, useful for curling

The counter lives in redis if REDIS_HOST is set. If redis is unreachable we
degrade to an in-process counter instead of 500ing. That is intentional: I'd
rather the app come up and log a warning than crash-loop because a sidecar is
slow to start.
"""

import os
import socket
import logging

from flask import Flask, jsonify, request

app = Flask(__name__)

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
log = logging.getLogger("flask-demo")

REDIS_HOST = os.environ.get("REDIS_HOST")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))
COUNTER_KEY = "flask-demo:hits"

_redis = None
_local_fallback = {"hits": 0}


def get_redis():
    """Lazily connect to redis. Returns None if it is not configured/reachable."""
    global _redis
    if _redis is not None:
        return _redis
    if not REDIS_HOST:
        return None
    try:
        import redis  # imported lazily so the app runs without the dep too

        client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            socket_connect_timeout=2,
            socket_timeout=2,
            decode_responses=True,
        )
        client.ping()
        _redis = client
        log.info("connected to redis at %s:%s", REDIS_HOST, REDIS_PORT)
    except Exception as exc:  # noqa: BLE001 - we genuinely want to swallow this
        log.warning("redis unavailable (%s), using in-process counter", exc)
        _redis = None
    return _redis


def bump() -> int:
    client = get_redis()
    if client is not None:
        try:
            return int(client.incr(COUNTER_KEY))
        except Exception as exc:  # noqa: BLE001
            log.warning("redis incr failed (%s), falling back", exc)
    _local_fallback["hits"] += 1
    return _local_fallback["hits"]


@app.get("/")
def index():
    hits = bump()
    return (
        "<!doctype html><html><head><title>docker-examples</title></head>"
        f"<body><h1>flask-demo</h1><p>hits: {hits}</p>"
        f"<p>host: {socket.gethostname()}</p></body></html>"
    )


@app.get("/health")
def health():
    # Liveness only. Never touch redis here or a redis blip will restart the app.
    return jsonify(status="ok")


@app.get("/count")
def count():
    client = get_redis()
    if client is not None:
        try:
            value = int(client.get(COUNTER_KEY) or 0)
            return jsonify(hits=value, backend="redis")
        except Exception as exc:  # noqa: BLE001
            log.warning("redis get failed: %s", exc)
    return jsonify(hits=_local_fallback["hits"], backend="memory")


@app.errorhandler(404)
def not_found(_):
    return jsonify(error="not found", path=request.path), 404


if __name__ == "__main__":
    # Dev server only. Production uses gunicorn (see Dockerfile CMD).
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
