# E-Commerce Backend API

A production-oriented e-commerce backend built with **FastAPI**, **PostgreSQL**, **SQLAlchemy**, **Alembic**, **JWT authentication**, **Docker**, and **GitHub Actions**.

The project follows a **Modular Monolith** architecture: one backend application, repository, and database, with business domains separated into modules.

## Features

- JWT authentication
- User registration and profiles
- Role-based access
- Address management
- Product and category management
- Shopping cart
- Checkout and order management
- Order state machine
- Inventory management
- Inventory reservation during checkout
- Payment flow with a mock provider
- Payment idempotency protection
- Transactional inventory updates
- Reservation expiration and inventory release
- Coupon management and discount calculation
- PostgreSQL
- Alembic migrations
- pytest test suite
- Docker and Docker Compose
- Development and production Compose configurations
- Docker health checks
- Automatic database migrations on startup
- Non-root API container
- GitHub Actions CI

## Architecture

```text
                    ┌──────────────────────┐
                    │      FastAPI API     │
                    └──────────┬───────────┘
                               │
       ┌───────────────────────┼───────────────────────┐
       │                       │                       │
     Auth                    Users                  Products
       │                       │                       │
   Categories              Addresses                 Cart
       │                       │                       │
       └───────────────────────┼───────────────────────┘
                               │
                    ┌──────────┴───────────┐
                    │        Orders        │
                    └───────┬───────┬──────┘
                            │       │
                     Reservations  Payments
                            │       │
                            └───┬───┘
                                │
                           Inventory
                                │
                         PostgreSQL
```

`Inventory` is implemented as an internal service rather than a public API domain.

## Project Structure

```text
ecommerce-backend/
│
├── app/
│   ├── auth/
│   ├── users/
│   ├── addresses/
│   ├── categories/
│   ├── products/
│   ├── cart/
│   ├── orders/
│   ├── payments/
│   ├── reservations/
│   ├── coupons/
│   ├── inventory/
│   ├── core/
│   └── main.py
│
├── alembic/
│   ├── versions/
│   └── env.py
│
├── tests/
├── .github/workflows/ci.yml
├── Dockerfile
├── docker-compose.yml
├── docker-compose.dev.yml
├── docker-compose.prod.yml
├── entrypoint.sh
├── pyproject.toml
├── uv.lock
└── alembic.ini
```

## Tech Stack

| Technology | Purpose |
|---|---|
| Python 3.13 | Programming language |
| FastAPI | Web framework |
| SQLAlchemy | ORM and database access |
| Pydantic | Validation and schemas |
| PostgreSQL | Relational database |
| Alembic | Database migrations |
| PyJWT | JWT authentication |
| bcrypt | Password hashing |
| pytest | Testing |
| uv | Dependency management |
| Docker | Containerization |
| Docker Compose | Multi-container environment |
| GitHub Actions | CI |

## Running Locally

Install dependencies:

```bash
uv sync
```

Create a local `.env` with the required application configuration. Never commit real secrets.

Run the API:

```bash
uv run uvicorn app.main:app --reload
```

API:

```text
http://localhost:8000
```

Health check:

```text
http://localhost:8000/health
```

Interactive documentation:

```text
http://localhost:8000/docs
```

## Docker Compose

### Development

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build
```

### Production-style configuration

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Stop services

```bash
docker compose down
```

To also remove the PostgreSQL volume:

```bash
docker compose down -v
```

> `docker compose down -v` removes the PostgreSQL Docker volume and its stored database data.

## Database Migrations

Alembic manages database migrations.

The migration chain currently ends at the reservations revision.

The API container automatically runs:

```bash
alembic upgrade head
```

before starting Uvicorn.

## Testing

Run the full test suite:

```bash
uv run pytest -q
```

Current test suite:

```text
297 tests
```

## CI

GitHub Actions runs on pushes to `main` and pull requests targeting `main`.

Current pipeline:

```text
Git Push / Pull Request
        ↓
GitHub Actions
        ↓
PostgreSQL service
        ↓
Python 3.13 + uv
        ↓
Install dependencies
        ↓
pytest
        ↓
Docker image build
```

The Docker build runs only after the test job succeeds.

## Docker

The project uses a multi-stage Docker build.

The runtime container:

- runs as a non-root user
- exposes port `8000`
- provides `/health`
- has a Docker `HEALTHCHECK`
- runs Alembic migrations on startup

## Current Status

The e-commerce backend and its infrastructure are in a working state, including:

- Modular Monolith architecture
- PostgreSQL persistence
- JWT authentication
- Transactional order and inventory flows
- Reservation and payment integration
- Automated tests
- Alembic migrations
- Docker containerization
- Docker Compose development/production configuration
- GitHub Actions CI

## Repository

GitHub: https://github.com/reza1381d/ecommerce
