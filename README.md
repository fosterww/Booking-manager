# Async Booking Service (High-Load Simulation)

A ticket booking microservice (cinema/events) designed to handle high-load scenarios. It implements robust protection against **Race Conditions** and double-booking issues.

## Key Features

* **Asynchronous:** Fully non-blocking I/O based on `asyncio` and `redis-py`.
* **Race Condition Protection:** Utilizes Redis atomic operations (`SET NX`) to prevent two users from booking the same seat simultaneously.
* **Temporary Reservation (TTL):** Seats are locked for 5 minutes. If the purchase is not completed, Redis automatically releases the slot.
* **Architecture:**
* **Dependency Injection:** Redis client is injected via `Depends`.
* **Pydantic Settings:** Strict configuration typing and environment variable management.
* **Graceful Shutdown:** Proper connection closure when the service stops.


* **DevOps:**
* Packaged in **Docker**.
* Deployed via **Kubernetes** (Deployment + Service).
* Configured **Liveness & Readiness Probes** for pod self-healing.


---

## 🛠️ Tech Stack

* **Language:** Python 3.10
* **Web Framework:** FastAPI
* **Database:** Redis (state management, locking, TTL)
* **Containerization:** Docker
* **Orchestration:** Kubernetes
* **Testing:** Pytest, TestClient, FakeRedis (Mock)

---

## Getting Started

### Option 1: Local Setup (No Docker)

Requires a running Redis instance on `localhost:6379`.

1. **Install dependencies:**
```bash
pip install fastapi uvicorn redis pydantic-settings

```


2. **Start the server:**
```bash
uvicorn main:app --reload

```


Swagger UI will be available at: `http://localhost:8000/docs`

---

### Option 2: Kubernetes (Recommended)

Ensure you have Docker installed and Kubernetes enabled (Minikube or Docker Desktop).

1. **Build the Docker image:**
```bash
docker build -t booking-app:v1 .

```


2. **Deploy to cluster:**
```bash
kubectl apply -f k8s-deployment.yaml

```


3. **Check status:**
```bash
kubectl get pods

```


*Wait until the pod status becomes `Running`. If it takes too long, check the logs.*
4. **Access the API:**
Open in browser: [http://localhost:8000/docs](https://www.google.com/search?q=http://localhost:8000/docs)
*Note for Minikube users: run `minikube service booking-service` to retrieve the correct URL.*

---

## 🧪 Testing

The project is covered by unit tests using mocks (FakeRedis), so a real database is **not required** to run tests.

1. **Install test dependencies:**
```bash
pip install pytest httpx pytest-asyncio

```


2. **Run tests:**
```bash
pytest test_main.py -v

```



---

## 🔌 API Usage Examples

### 1. Reserve a Seat

Blocks the seat for 5 minutes (TTL).

**POST** `/reserve`

```json
{
  "seat_id": "1A",
  "user_id": "user_123"
}

```

* **200 OK**: `{"status": "reserved"}` — Successful.
* **409 Conflict**: Seat is already occupied by another user.

### 2. Confirm Purchase (Buy)

Purchase is only possible if the user holds an active reservation for the seat.

**POST** `/buy`

```json
{
  "seat_id": "1A",
  "user_id": "user_123"
}

```

* **200 OK**: `{"status": "sold"}` — Successful, status changed to permanent.
* **400 Bad Request**: Reservation expired or belongs to a different user.

### 3. Get Seat Status

**GET** `/seats/{seat_id}`

* Returns: `Available`, `Reserved`, or `Sold`.

---

## Project Structure

```text
.
├── main.py             # Entry point, FastAPI initialization, and business logic
├── config.py           # Configuration management (Pydantic Settings)
├── k8s-deployment.yaml # Kubernetes manifests (Redis + App + Services)
├── Dockerfile          # Image build instructions
├── test_main.py        # Tests with dependency mocking
├── requirements.txt    # List of dependencies
└── README.md           # Project documentation

```
