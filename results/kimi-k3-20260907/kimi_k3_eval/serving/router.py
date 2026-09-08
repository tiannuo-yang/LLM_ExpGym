"""OpenAI-compatible transparent least-inflight router for four owned replicas."""
import argparse
import asyncio
import contextlib
import json
import time
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response, StreamingResponse

parser = argparse.ArgumentParser()
parser.add_argument("--deployment", type=Path, required=True)
args = parser.parse_args()
deployment = json.loads(args.deployment.read_text())
backends = [{**r, "healthy": False, "inflight": 0, "last_used": 0.0} for r in deployment["replicas"]]
client = httpx.AsyncClient(timeout=httpx.Timeout(1800.0, connect=10.0), trust_env=False,
                          limits=httpx.Limits(max_connections=512, max_keepalive_connections=128))

async def refresh_health():
    async def check(backend):
        try:
            response = await client.get(backend["url"] + "/health", timeout=5)
            backend["healthy"] = response.status_code == 200
        except httpx.HTTPError:
            backend["healthy"] = False
    while True:
        await asyncio.gather(*(check(backend) for backend in backends))
        await asyncio.sleep(5)

@asynccontextmanager
async def lifespan(app):
    task = asyncio.create_task(refresh_health())
    yield
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task
    await client.aclose()

app = FastAPI(lifespan=lifespan)

@app.get("/health")
async def health():
    healthy = sum(b["healthy"] for b in backends)
    return JSONResponse({"healthy_replicas": healthy, "total_replicas": len(backends),
                         "job_id": deployment["job_id"], "backends": backends},
                        status_code=200 if healthy else 503)

@app.api_route("/{path:path}", methods=["GET", "POST"])
async def proxy(path: str, request: Request):
    choices = [b for b in backends if b["healthy"]]
    if not choices:
        return JSONResponse({"error": "All replicas are still loading or unhealthy"}, status_code=503)
    backend = min(choices, key=lambda b: (b["inflight"], b["last_used"]))
    backend["inflight"] += 1
    backend["last_used"] = time.time()
    payload = await request.body()
    headers = {k: v for k, v in request.headers.items()
               if k.lower() not in {"host", "content-length", "connection"}}
    url = backend["url"] + "/" + path
    if request.url.query:
        url += "?" + request.url.query
    try:
        upstream = await client.send(client.build_request(request.method, url, content=payload,
                                                          headers=headers), stream=True)
    except httpx.HTTPError as exc:
        backend["inflight"] -= 1
        backend["healthy"] = False
        return JSONResponse({"error": "upstream transport failure", "detail": type(exc).__name__,
                             "replica": backend["replica"]}, status_code=502)
    result_headers = {"X-K3-Replica": str(backend["replica"])}
    for name in ("content-type", "content-encoding"):
        if name in upstream.headers:
            result_headers[name] = upstream.headers[name]
    async def stream():
        try:
            async for chunk in upstream.aiter_raw():
                yield chunk
        finally:
            await upstream.aclose()
            backend["inflight"] -= 1
    return StreamingResponse(stream(), status_code=upstream.status_code, headers=result_headers)

uvicorn.run(app, host="0.0.0.0", port=30141, log_level="info")
