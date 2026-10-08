# E-Commerce Storefront

The storefront is a React and TypeScript single-page application built with Vite. It includes customer shopping flows and the administrator dashboard.

## Requirements

- Node.js 22.22.2 or newer, or Node.js 24.15 or newer
- The FastAPI backend and PostgreSQL database running locally

## Install and run

From this directory, install the locked dependencies and start the development server:

```powershell
npm ci
npm run dev
```

The default backend address is `http://localhost:8000`. To use a different address, copy `.env.example` to `.env` and set `VITE_API_BASE_URL`:

```env
VITE_API_BASE_URL=http://localhost:8000
```

Vite reads this value when it starts, so restart the development server after changing it. Do not put private credentials in frontend environment variables; values prefixed with `VITE_` are included in the browser build.

## Checks

Run the frontend tests:

```powershell
npm test
```

Create the production build:

```powershell
npm run build
```

Run Oxlint:

```powershell
npm run lint
```

The current tests cover currency conversion and whole-number formatting, Gregorian/Jalali conversion and preference persistence, and favorites state persistence. Component tests use Vitest, jsdom, and Testing Library.

## Main application areas

- `src/api/` contains typed calls to backend endpoints.
- `src/context/` contains authentication, cart, date format, favorites, and store settings state.
- `src/pages/` contains storefront and admin pages.
- `src/layouts/` contains the storefront and admin navigation shells.
- `src/utils/` contains shared currency helpers.
