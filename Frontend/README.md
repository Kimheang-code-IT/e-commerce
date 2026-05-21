# PDME-Revenue Operations Management Platform

**PDME-Revenue** is an advanced, enterprise-grade frontend platform designed for Customs and Excise Cambodia management systems. 

## Technology Stack

The application has been engineered for maximum scalability, adhering to modern best practices:
- **Core Engine:** Nuxt 4, Vue 3, Composition API
- **UI Framework & Styling:** Nuxt UI v3 (Pro features enabled), TailwindCSS v4
- **State Management:** Pinia
- **Tables & Grids:** TanStack Vue Table v8
- **Data Visualization:** Apache ECharts
- **Internationalization:** `@nuxtjs/i18n` with support for English (`en`) and Khmer (`km`). Advanced typography overrides ensure "Siemreap" is injected for optimal Khmer rendering.

## Current Architectural State

The UI is integrated with backend APIs through `app/utils/api/` and `useApi()`.
- Data tables consume server-driven resources from backend endpoints.
- Export flows use unified `CommonAppExport` and currently request JSON data for client-side CSV generation.
- Backend mode is controlled with environment variables in `.env`.

## Future Improvement & API Roadmap
1. Add server-provided CSV file download mode as an option in export modal.
2. Add production Nuxt build container/profile (`pnpm build && pnpm preview`) for deployment.
3. Expand route-level role rules for finer customer/staff/admin page visibility.
4. Add stronger form schema validation with Zod.

## API-First Frontend Policy

- Frontend should not own authoritative business logic, pricing rules, or persistent CRUD rules.
- `app/data/*` files are temporary mock sources only until backend endpoints are ready.
- New feature work should use API clients in `app/utils/api/` and `useApi()` wrapper.
- Toggle backend mode with:
  - `NUXT_PUBLIC_USE_BACKEND_API=true`
  - `NUXT_PUBLIC_API_BASE=/api/v1`

---

## Setup & Development

Make sure to install the dependencies:

```bash
pnpm install
```

Start the development server on `http://localhost:3000`:

```bash
pnpm dev
```

## Production

Build the application for production:

```bash
pnpm build
```

Locally preview production build:

```bash
pnpm preview
```
