# Kanka Frontend

Next.js 16 (App Router) + React 19 + Tailwind v4.

## Geliştirme

```bash
npm install
cp .env.example .env.local
npm run dev   # http://localhost:3000
```

`NEXT_PUBLIC_API_BASE` backend URL'idir (default: `http://localhost:8765`).

## Üretim build

```bash
npm run build
npm start -- -p 3000
```
