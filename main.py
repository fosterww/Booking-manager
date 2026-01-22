import os
import logging

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel

from enum import Enum
import redis.asyncio as redis
from config import settings


logger = logging.getLogger(__name__)

redis_pool = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_pool
    logger.info(f"Connecting to Redis at {settings.redis_host}...")
    redis_pool = redis.from_url(f"redis://{settings.redis_host}:{settings.redis_port}", decode_responses=True)
    yield
    logger.info("Closing Redis connection...")
    await redis_pool.close()


app = FastAPI(lifespan=lifespan)

async def get_redis():
    if redis_pool is None:
        raise HTTPException(500, "Redis not connected")
    return redis_pool

class SeatStatus(Enum):
    AVAILABLE = "Available"
    RESERVED = "Reserved"
    SOLD = "Sold"

class RequestDTO(BaseModel):
    seat_id: str
    user_id: str


class RedisBookingSystem:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        
    async def reserve(self, seat_id: str, user_id: str) -> bool:
        if await self.redis.get(f"sold:{seat_id}"):
            return False
        success = await self.redis.set(f"booking:{seat_id}", user_id, ex=300, nx=True)
        return bool(success)

    async def purchase(self, seat_id: str, user_id: str) -> bool:
        current_owner = await self.redis.get(f"booking:{seat_id}")
        if current_owner != user_id:
            return False
        
        async with self.redis.pipeline(transaction=True) as pipe:
            try:
                await pipe.set(f"sold:{seat_id}", "true")
                await pipe.delete(f"booking:{seat_id}")
                await pipe.execute()
                return True
            except Exception:
                return False
                
    async def get_status(self, seat_id: str) -> str:
        if await self.redis.get(f"sold:{seat_id}"):
            return SeatStatus.SOLD.value
        if await self.redis.get(f"booking:{seat_id}"):
            return SeatStatus.RESERVED.value
        return SeatStatus.AVAILABLE.value


@app.get("/health")
async def health_check():
    if redis_pool is None:
        raise HTTPException(503, "Not ready")
    return {"status": "ok"}

@app.get("/seats/{seat_id}")
async def get_seat_endpoint(seat_id: str, r = Depends(get_redis)):
    system = RedisBookingSystem(r)
    status = await system.get_status(seat_id)
    return {"seat_id": seat_id, "status": status}

@app.post("/reserve")
async def reserve_endpoint(req: RequestDTO, r = Depends(get_redis)):
    system = RedisBookingSystem(r)
    if await system.reserve(req.seat_id, req.user_id):
        return {"status": "reserved"}
    raise HTTPException(409, "Already taken")

@app.post("/buy")
async def buy_endpoint(req: RequestDTO, r = Depends(get_redis)):
    system = RedisBookingSystem(r)
    if await system.purchase(req.seat_id, req.user_id):
        return {"status": "sold"}
    raise HTTPException(400, "Reservation expired or invalid user")