import pytest
from fastapi.testclient import TestClient

import main
from main import app, get_redis

class FakeRedis:
    def __init__(self):
        self.data = {}

    async def get(self, key):
        return self.data.get(key)
    
    async def set(self, key, value, ex=None, nx=False):
        if nx and key in self.data:
            return False
        self.data[key] = value
        return True
    
    def pipeline(self, transaction=True):
        return self
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_value, traceback):
        pass

    async def delete(self, key):
        if key in self.data:
            del self.data[key]

    async def execute(self):
        pass

    async def close(self):
        pass

fake_redis = FakeRedis()

async def override_get_redis():
    return fake_redis

app.dependency_overrides[get_redis] = override_get_redis
client = TestClient(app)

main.redis_pool = fake_redis

def test_health_check():
    resp = client.get('/health')
    assert resp.status_code == 200
    assert resp.json() == {'status': 'ok'}

def test_reserve():
    payload = {'seat_id': '1A', "user_id": "Alice"}
    resp = client.post("/reserve", json=payload)
    assert resp.status_code == 200
    assert resp.json() == {'status': 'reserved'}

    resp = client.get("/seats/1A")
    assert resp.json()["status"] == 'Reserved'

    response = client.post("/reserve", json=payload)
    assert response.status_code == 409

def test_purchase_flow():
    client.post("/reserve", json={"seat_id": "2B", "user_id": "Bob"})
    
    response = client.post("/buy", json={"seat_id": "2B", "user_id": "Bob"})
    assert response.status_code == 200
    assert response.json() == {"status": "sold"}
    
    response = client.get("/seats/2B")
    assert response.json()["status"] == "Sold"