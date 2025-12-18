Proyecto: Image Search (Frontend Angular + Backend FastAPI)

Estructura:
- frontend/: proyecto Angular básico (componentes para subir y buscar imagenes)
- backend/: API en FastAPI con endpoints `/upload` y `/search` 

Instrucciones rápidas:

Backend:
1. Abrir terminal en `backend`
2. Crear y activar un entorno virtual (opcional)

Windows PowerShell:
```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Frontend:
1. Instalar Node.js y Angular CLI
2. Abrir terminal en `frontend`
```
npm install
npx ng serve --open
```

Notas:
- El endpoint del frontend asume que la API está disponible en `/api/*`. Para desarrollo configure un proxy o use rutas absolutas `http://localhost:8000`.
- La búsqueda por similitud aún no está implementada; el endpoint `/search` devuelve resultados de ejemplo.
- Este repositorio incluye una carpeta /sitios/ (~100 MB) con imágenes de prueba para facilitar la reproducción.
