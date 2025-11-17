# PetCam Frontend (React + Vite)

Simple React UI to browse PetCam snapshots via the Flask backend API.

## Setup

```bash
cd PetCam/frontend
npm install
npm run dev -- --host
```

Open http://localhost:5173 (or the host shown in the console).

## Config

Set the backend URL via env (optional). Default is http://localhost:5000/api.

```bash
# .env.local
VITE_API_BASE=http://localhost:5000/api
```

## Build

```bash
npm run build
npm run preview
```

## Notes

- The UI calls `/latest` and `/list` endpoints. Ensure the backend is running and has images (run the capture loop or stubbed generator). 
- When serving in prod, place the built `dist/` behind your web server and proxy API calls to the Flask backend. 
