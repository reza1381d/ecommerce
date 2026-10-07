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
- Docker image publishing
- Production deployment infrastructure

## Architecture

                    ┌──────────────────────┐
                    │      FastAPI API     │
                    └──────────┬───────────┘
                               │
       ┌───────────────────────┼───────────────────────┐
       │                       │                       │
     Auth                    Users                 Products
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

`Inventory` is implemented as an internal service rather than a public API domain.

## Project Structure

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
    ├── deploy.sh
    ├── entrypoint.sh
    ├── .env.example
    ├── pyproject.toml
    ├── uv.lock
    └── alembic.ini

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
| GitHub Actions | CI and image publishing |

## Running Locally

Install dependencies:

    uv sync

Create a local `.env` file based on `.env.example`:

    Copy-Item .env.example .env

Then replace the placeholder values in `.env` with your local configuration.

Required environment variables:

    DATABASE_URL=postgresql+psycopg://USERNAME:PASSWORD@localhost:5432/ecommerce
    JWT_SECRET_KEY=CHANGE_ME_TO_A_RANDOM_SECRET
    JWT_ALGORITHM=HS256
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

Never commit `.env` or any real secrets.

Run the API:

    uv run uvicorn app.main:app --reload

API:

    http://localhost:8000

Health check:

    http://localhost:8000/health

Interactive documentation:

    http://localhost:8000/docs

## Docker Compose

### Development

    docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build

### Production-style configuration

    docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

### Stop services

    docker compose down

To also remove the PostgreSQL volume:

    docker compose down -v

> `docker compose down -v` removes the PostgreSQL Docker volume and its stored database data.

## Database Migrations

Alembic manages database migrations.

The migration chain currently ends at the reservations revision.

The API container automatically runs:

    alembic upgrade head

before starting Uvicorn.

## Testing

Run the full test suite:

    uv run pytest -q

Current test suite:

    297 tests

## CI

GitHub Actions runs on pushes to `main` and pull requests targeting `main`.

Current pipeline:

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
            ↓
    Docker image push

The Docker build runs only after the test job succeeds.

On pushes to `main`, the successfully built Docker image is pushed to Docker Hub using the Git commit SHA as the image tag.

Example image tag:

    <dockerhub-username>/ecommerce-api:<git-sha>

Pull requests run the test and Docker build stages but do not push an image.

## Docker

The project uses a multi-stage Docker build.

The runtime container:

- runs as a non-root user
- exposes port `8000`
- provides `/health`
- has a Docker `HEALTHCHECK`
- runs Alembic migrations on startup

## Production Deployment

The project supports an image-based production deployment using Docker Compose.

Production consists of:

    GitHub Actions
          ↓
    Docker Image
          ↓
    Docker Hub
          ↓
    VPS
          ↓
    Docker Compose
          ↓
    FastAPI + PostgreSQL

The production API runs as a Docker container and PostgreSQL runs as a separate container.

The production Compose configuration uses a specific Docker image tag:

    IMAGE_TAG=<git-sha> docker compose \
      -f docker-compose.yml \
      -f docker-compose.prod.yml \
      up -d

The repository also contains:

    deploy.sh

The deployment script:

1. Pulls the requested API image.
2. Starts or updates the production services.
3. Displays the production service status.
4. Uses Docker health checks to verify service health.

Example:

    IMAGE_TAG=<git-sha> sh deploy.sh

### Production Environment

Production secrets are stored only on the VPS in `.env`.

The production `.env` file is never committed to Git.

The production database connection uses the Docker Compose service name:

    postgres

instead of `localhost`.

### Production Health Check

The API exposes:

    /health

Example response:

    HTTP/1.1 200 OK

    {"status":"ok"}

Interactive API documentation is available through:

    /docs

### Current Production Status

The production environment has been successfully deployed to a VPS.

The following components have been verified:

- PostgreSQL container is healthy
- API container is healthy
- Alembic migrations run successfully on startup
- FastAPI listens on port `8000`
- `/health` responds successfully from the public internet
- `/docs` responds successfully from the public internet
- Docker image is pulled from Docker Hub
- Production environment variables are stored outside Git
- Production Docker Compose configuration works successfully

The current deployment is image-based and can be performed manually using the production Docker Compose configuration and `deploy.sh`.

Automatic VPS deployment from GitHub Actions is not enabled yet.

## Production Network Security

The VPS uses multiple firewall layers:

    Internet
       ↓
    Provider Security Group
       ↓
    UFW
       ↓
    Docker
       ↓
    FastAPI

The provider-level security group and the VPS firewall are configured independently.

During the initial production deployment, TCP port `8000` was opened at both firewall layers for direct API verification.

The current application endpoint is:

    http://<server-ip>:8000

The VPS currently allows:

    22/tcp    SSH
    8000/tcp  API

The provider security group also allows TCP port `8000` for the current deployment verification.

For the final production architecture, the API should be placed behind a reverse proxy:

    Internet
        ↓
    80 / 443
        ↓
    Reverse Proxy
        ↓
    127.0.0.1:8000
        ↓
    FastAPI

After the reverse proxy and HTTPS configuration are completed, direct public access to port `8000` should be removed.

## Environment Configuration

The repository provides `.env.example` as a template for required environment variables.

Example:

    DATABASE_URL=postgresql+psycopg://USERNAME:PASSWORD@localhost:5432/ecommerce
    JWT_SECRET_KEY=CHANGE_ME_TO_A_RANDOM_SECRET
    JWT_ALGORITHM=HS256
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

Production secrets are configured directly on the VPS and are excluded from Git.

Never commit:

    .env
    .env.test

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
- Docker health checks
- Automatic database migrations on startup
- Non-root API container
- GitHub Actions CI
- Docker image publishing
- Production VPS deployment
- Production health verification
- Environment configuration via `.env` and `.env.example`

Current production deployment is image-based and can be performed manually using the production Docker Compose configuration and `deploy.sh`.

The next infrastructure step is to automate VPS deployment from GitHub Actions, followed by reverse proxy and HTTPS configuration.

## Repository

GitHub:

https://github.com/reza1381d/ecommerce