# E-Commerce Backend API

A production-oriented e-commerce application built with **FastAPI**, **PostgreSQL**, **SQLAlchemy**, **Alembic**, **JWT authentication**, **Docker**, **GitHub Actions**, and a **React + TypeScript frontend**.

The project follows a **Modular Monolith** architecture: one backend application, repository, and database, with business domains separated into modules.

---

## Features

### Backend

- JWT authentication
- User registration and profiles
- Role-based access control
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
- Admin order, user, and payment management
- Pagination, filtering, search, and sorting
- Accounting reports
- Store settings management
- Product image upload and removal
- Toman/rial currency handling
- PostgreSQL persistence
- Alembic migrations
- Automated database migrations on startup
- Docker health checks
- Non-root API container
- Production Docker deployment
- GitHub Actions CI/CD
- Docker image publishing

### Frontend

- React
- TypeScript
- Vite
- Tailwind CSS
- Vitest
- Testing Library
- Storefront pages
- Product listing and details
- Categories
- Favorites
- Authentication
- Shopping cart
- Checkout
- Orders
- Payments
- Account management
- Address management
- Admin dashboard
- Admin product management
- Admin category management
- Admin coupon management
- Admin order management
- Admin user management
- Admin payment management
- Admin store settings

---

## Architecture

```text
                         Internet
                            │
                            ▼
                    rezadastoori.ir
                            │
                       Nginx :443
                            │
                            ▼
                    FastAPI :8000
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
       Auth                Users             Products
        │                   │                   │
   Categories          Addresses             Cart
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
                         Orders
                       ┌────┴────┐
                       │         │
                 Reservations  Payments
                       │         │
                       └────┬────┘
                            │
                        Inventory
                            │
                            ▼
                       PostgreSQL
```

`Inventory` is an internal service rather than a public API domain.

Admin endpoints remain with their related domains:

```text
/admin/orders
/admin/users
/admin/payments
/admin/store/settings
```

Sales reporting is provided by the `accounting` module under:

```text
/admin/dashboard/*
```

---

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
│   ├── accounting/
│   ├── store_settings/
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
│
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   ├── vite.config.ts
│   └── ...
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
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
```

---

## Tech Stack

| Technology | Purpose |
|---|---|
| Python 3.13 | Backend language |
| FastAPI | Web framework |
| SQLAlchemy | ORM and database access |
| Pydantic | Validation and schemas |
| PostgreSQL | Relational database |
| Alembic | Database migrations |
| PyJWT | JWT authentication |
| bcrypt | Password hashing |
| pytest | Backend testing |
| React | Frontend UI |
| TypeScript | Frontend language |
| Vite | Frontend build tooling |
| Tailwind CSS | Frontend styling |
| Vitest | Frontend testing |
| Testing Library | Frontend component testing |
| uv | Python dependency management |
| Docker | Containerization |
| Docker Compose | Multi-container environments |
| GitHub Actions | CI/CD |
| Nginx | Production reverse proxy |
| Let's Encrypt | TLS certificate |
| Certbot | Automatic certificate management |

---

# Backend

## Running Locally

Install dependencies:

```bash
uv sync
```

Create `.env` from `.env.example`.

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Required configuration includes:

```env
DATABASE_URL=postgresql+psycopg://USERNAME:PASSWORD@localhost:5432/ecommerce
JWT_SECRET_KEY=CHANGE_ME_TO_A_RANDOM_SECRET
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
```

Never commit `.env` or real secrets.

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

---

## Docker Compose

### Development

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build
```

### Production-style Compose

```bash
IMAGE_TAG=<git-sha> docker compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  up -d
```

### Stop services

```bash
docker compose down
```

Remove PostgreSQL volume:

```bash
docker compose down -v
```

> `docker compose down -v` removes the PostgreSQL Docker volume and its stored database data.

---

## Database Migrations

Alembic manages database migrations.

The API container automatically runs:

```bash
alembic upgrade head
```

before starting Uvicorn.

Migration history includes features such as:

- Product images
- Store name
- Color palette
- Currency
- Home-page settings

---

## Testing

### Backend

The backend suite uses a dedicated PostgreSQL test database configured through `.env.test`.

Run:

```bash
uv run pytest -q
```

The test suite covers:

- Authentication
- Users
- Addresses
- Categories
- Products
- Cart
- Orders
- Checkout
- Inventory
- Reservations
- Payments
- Coupons
- Admin APIs
- Store settings
- Product images
- Accounting reports

The production development workflow uses:

```bash
python -m pytest
```

when the virtual environment's direct `pytest` launcher is unavailable.

---

# Frontend

The project contains a React/TypeScript storefront and admin interface under:

```text
frontend/
```

## Frontend Stack

```text
React
TypeScript
Vite
Tailwind CSS
Vitest
Testing Library
```

## Frontend Development

From the project root:

```bash
cd frontend
npm ci
npm run dev
```

The development frontend uses the backend API configured through:

```env
VITE_API_BASE_URL=http://localhost:8000
```

If the variable is not provided, the frontend API client falls back to:

```text
http://localhost:8000
```

## Frontend Tests

```bash
cd frontend
npm ci
npm test
```

Frontend tests cover areas including:

- Currency formatting and conversion
- Calendar conversion
- Preference persistence
- Favorites persistence
- Component behavior

## Frontend Production Build

```bash
cd frontend
npm run build
```

The production build is generated by Vite.

The build was verified successfully during development.

---

## Frontend Routes

Main storefront routes include:

```text
/
 /products
 /products/:productId
 /category/:category
 /favorites
 /login
 /register
 /cart
 /checkout
 /account
 /orders
 /payments
```

Admin routes include:

```text
/admin
/admin/products
/admin/categories
/admin/coupons
/admin/orders
/admin/users
/admin/payments
/admin/settings
```

The frontend is currently maintained as a separate application from the backend API.

Its final production hosting/reverse-proxy integration is intentionally left as a separate deployment step.

---

# API Overview

Important backend endpoints include:

| Area | Endpoint | Purpose |
|---|---|---|
| Store settings | `GET /store/settings` | Public store configuration |
| Store settings | `PUT /admin/store/settings` | Admin store configuration |
| Orders | `GET /admin/orders` | Paginated admin orders |
| Users | `GET /admin/users` | Paginated users |
| Payments | `GET /admin/payments` | Paginated payments |
| Accounting | `GET /admin/dashboard/stats` | Sales/order summary |
| Accounting | `GET /admin/dashboard/product-sales` | Product sales |
| Accounting | `GET /admin/dashboard/sales-timeline` | Sales timeline |
| Product images | `POST /products/{product_id}/image` | Upload product image |
| Product images | `DELETE /products/{product_id}/image` | Remove product image |

Uploaded images are served from:

```text
/uploads/products/
```

---

# CI/CD

GitHub Actions runs on:

- Pushes to `main`
- Pull requests targeting `main`

The pipeline is approximately:

```text
Git Push / Pull Request
          │
          ▼
    GitHub Actions
          │
          ▼
   PostgreSQL service
          │
          ▼
 Python 3.13 + uv
          │
     ┌────┴────┐
     │         │
  Backend   Frontend
   tests      tests
     │         │
     │      lint/build
     └────┬────┘
          │
          ▼
     Docker Build
          │
          ▼
     Docker Hub
```

The Docker image is built only after the test job succeeds.

On pushes to `main`, the image is pushed using the Git commit SHA as the image tag:

```text
<dockerhub-username>/ecommerce-api:<git-sha>
```

Pull requests run the validation and build stages without publishing a production image.

---

# Docker

The backend uses a multi-stage Docker build.

The runtime container:

- Uses Python 3.13
- Runs as a non-root user
- Exposes port `8000` internally
- Provides `/health`
- Has a Docker `HEALTHCHECK`
- Runs Alembic migrations on startup
- Uses persistent storage for product images

Production PostgreSQL runs as a separate Docker Compose service.

---

# Production Deployment

The production deployment is image-based.

Architecture:

```text
GitHub Actions
      │
      ▼
 Docker Image
      │
      ▼
 Docker Hub
      │
      ▼
    VPS
      │
      ▼
 Docker Compose
      │
 ┌────┴────┐
 │         │
FastAPI  PostgreSQL
```

The production environment uses:

```text
/opt/ecommerce
```

on the VPS.

The API image is identified by the exact Git commit SHA that triggered the deployment.

Example:

```bash
IMAGE_TAG=<git-sha> sh deploy.sh
```

The deployment script:

1. Pulls the requested API image.
2. Starts or updates production services.
3. Displays service status.
4. Relies on Docker health checks to verify service health.

---

# Automatic VPS Deployment

Production deployment is automated through GitHub Actions.

On a push to `main`:

```text
Git Push
   ↓
Tests
   ↓
Docker Build
   ↓
Docker Image Push
   ↓
SSH to VPS
   ↓
Git Pull
   ↓
Production Deployment
   ↓
Health Check
```

The VPS deployment uses the exact Git commit SHA as the Docker image tag.

No production secrets are stored in the repository.

The production environment uses secrets configured outside Git.

---

# Production DNS

Production domain:

```text
rezadastoori.ir
```

WWW domain:

```text
www.rezadastoori.ir
```

Both currently resolve to the production VPS:

```text
94.183.176.177
```

The authoritative DNS nameservers are:

```text
breeze.parspack.net
wood.parspack.net
```

Verified DNS resolution:

```text
rezadastoori.ir      → 94.183.176.177
www.rezadastoori.ir → 94.183.176.177
```

---

# Production Reverse Proxy

Nginx is used as the production reverse proxy.

The production request flow is:

```text
Internet
   │
   ▼
rezadastoori.ir
   │
   ├── HTTP :80
   │       │
   │       ▼
   │   HTTPS redirect
   │
   └── HTTPS :443
           │
           ▼
        Nginx
           │
           ▼
   127.0.0.1:8000
           │
           ▼
        FastAPI
```

FastAPI continues to listen internally on port `8000`.

Port `8000` is **not publicly exposed through the VPS firewall**.

---

# HTTPS / TLS

HTTPS is enabled using:

```text
Let's Encrypt
Certbot
```

The certificate covers:

```text
rezadastoori.ir
www.rezadastoori.ir
```

Certificate renewal is configured automatically through Certbot.

HTTP requests are redirected to HTTPS:

```text
http://rezadastoori.ir
        ↓
301
        ↓
https://rezadastoori.ir
```

The public health endpoint is:

```text
https://rezadastoori.ir/health
```

Expected response:

```json
{
  "status": "ok"
}
```

HTTPS has been verified successfully from outside the VPS.

---

# Production Network Security

The final production network architecture is:

```text
                    Internet
                       │
              ┌────────┴────────┐
              │                 │
            :80               :443
              │                 │
              ▼                 ▼
          Nginx HTTP        Nginx HTTPS
              │                 │
              └────────┬────────┘
                       │
                       ▼
                 127.0.0.1:8000
                       │
                       ▼
                    FastAPI
                       │
                       ▼
                  PostgreSQL
```

The final UFW configuration is:

```text
22/tcp    ALLOW   SSH
80/tcp    ALLOW   HTTP / HTTPS redirect
443/tcp   ALLOW   HTTPS
8000/tcp  CLOSED  Public access
```

Port `8000` remains the internal FastAPI application port, but it is no longer publicly accessible.

This means external users must access the application through Nginx and HTTPS.

---

# Production Verification

The following production components have been verified:

- PostgreSQL container is healthy
- API container is healthy
- Alembic migrations run successfully on startup
- FastAPI listens on port `8000`
- DNS resolves correctly
- Nginx is running
- HTTP reverse proxy works
- HTTP redirects to HTTPS
- HTTPS certificate is valid
- HTTPS reverse proxy works
- `/health` responds successfully from the public internet
- `/docs` is available through the production API
- Docker image is pulled from Docker Hub
- Production environment variables remain outside Git
- Production Docker Compose configuration works
- Public access to port `8000` has been removed
- UFW exposes only SSH, HTTP, and HTTPS

Verified public health endpoint:

```text
https://rezadastoori.ir/health
```

Expected response:

```json
{"status":"ok"}
```

---

# Production Environment Configuration

Production secrets are stored only on the VPS in:

```text
.env
```

The production `.env` file is never committed to Git.

The production database connection uses the Docker Compose service name:

```text
postgres
```

instead of:

```text
localhost
```

Never commit:

```text
.env
.env.test
```

or any other file containing real credentials or private keys.

---

# Current Production Status

The e-commerce backend and its infrastructure are in a working production state, including:

- Modular Monolith architecture
- PostgreSQL persistence
- JWT authentication
- Transactional order and inventory flows
- Reservation and payment integration
- Automated backend tests
- Alembic migrations
- Docker containerization
- Docker Compose development/production configuration
- Docker health checks
- Automatic database migrations
- Non-root API container
- GitHub Actions CI
- Docker image publishing
- Automatic VPS deployment
- Production VPS deployment
- DNS configuration
- Nginx reverse proxy
- HTTPS
- Automatic TLS renewal
- Production health verification
- Firewall hardening
- Public API protection through reverse proxy
- Frontend application and tests
- Production frontend build verification

---

# Frontend Production Status

The frontend application has been implemented and integrated with the backend API.

The frontend includes:

- Storefront UI
- Authentication
- Products
- Categories
- Favorites
- Cart
- Checkout
- Orders
- Payments
- Account
- Admin dashboard
- Admin products
- Admin categories
- Admin coupons
- Admin orders
- Admin users
- Admin payments
- Admin settings

Frontend validation completed successfully with:

```text
3 test files
7 tests passed
```

Production build completed successfully with:

```bash
tsc -b && vite build
```

The frontend is currently kept as a separate application from the production backend deployment.

Its final production hosting and same-origin routing configuration will be handled as a separate deployment phase.

---

# Security Notes

The project follows several production security practices:

- JWT-based authentication
- Password hashing with bcrypt
- Role-based authorization
- Environment-based secrets
- Secrets excluded from Git
- Non-root Docker runtime
- PostgreSQL not publicly exposed
- FastAPI port `8000` not publicly exposed after reverse proxy setup
- HTTPS enabled
- Automatic certificate renewal
- UFW firewall
- SSH key authentication
- SSH password authentication disabled
- Root SSH login disabled

---

# Current Status

The backend application and production infrastructure are currently operational.

Completed:

```text
Backend
   ✅

Database
   ✅

Migrations
   ✅

Authentication
   ✅

Orders
   ✅

Inventory
   ✅

Reservations
   ✅

Payments
   ✅

Coupons
   ✅

Admin APIs
   ✅

Accounting
   ✅

Product Images
   ✅

Frontend
   ✅

Frontend Tests
   ✅

Frontend Build
   ✅

Docker
   ✅

GitHub Actions
   ✅

Docker Hub
   ✅

VPS Deployment
   ✅

DNS
   ✅

Nginx Reverse Proxy
   ✅

HTTPS
   ✅

Firewall Hardening
   ✅
```

The current public API is available through:

```text
https://rezadastoori.ir
```

Health check:

```text
https://rezadastoori.ir/health
```

Interactive documentation:

```text
https://rezadastoori.ir/docs
```

---

# Repository

GitHub:

```text
https://github.com/reza1381d/ecommerce
```