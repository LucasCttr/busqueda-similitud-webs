"""
main.py
---------
Backend principal de la aplicación de búsqueda de imágenes por similitud.

Responsabilidades:
- Expone endpoints para subir imágenes y buscar imágenes similares.
- Gestiona el almacenamiento de imágenes en disco.
- Mantiene y persiste los features de imágenes y sus rutas en un archivo pickle y un índice FAISS.
- Inicializa el modelo de extracción de features al arrancar para evitar latencia en la primera búsqueda.

Endpoints principales:
- POST /upload: Sube una imagen, extrae sus features y la agrega al índice.
- POST /search: Busca imágenes similares a una imagen dada.
- GET /sitios/<archivo>: Sirve las imágenes almacenadas.

Fuente de verdad: El archivo pickle y el índice FAISS.
No se usa base de datos relacional.
"""
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'


from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi import Request
from pathlib import Path
import shutil
import uuid
import faiss, pickle, numpy as np
from features.features import extract_mixed_features, _ensure_model
from io import BytesIO
from PIL import Image

_ensure_model()  # Inicializa el modelo de features al arrancar
# Cargar índice FAISS
INDEX_PATH = Path(__file__).parent / "models/faiss_index.idx"
index = faiss.read_index(str(INDEX_PATH))

# Cargar features y paths
with open(Path(__file__).parent / "models/dataset_1_Layers_avg_pool.pkl", "rb") as f:
    data = pickle.load(f)
dataset_features = list(data["features"])
dataset_paths = data["paths"]

# Normalizar rutas y limpiar entradas sin archivo físico
def _clean_dataset_and_index():
    """
    Limpia el dataset y el índice FAISS eliminando entradas cuyos archivos no existen.
    Persiste el resultado limpio en el pickle y el índice FAISS.
    """
    global dataset_features, dataset_paths
    valid_feats = []
    valid_paths = []
    for feat, path in zip(dataset_features, dataset_paths):
        fname = Path(path).name
        rel = str(Path("sitios") / fname).replace("\\", "/")
        full_path = Path(__file__).parent / rel
        if full_path.exists():
            valid_feats.append(feat)
            valid_paths.append(path)
        else:
            print(f"[CLEAN] Eliminando entrada sin archivo físico: {path}")
    # Solo actualiza en memoria, no persiste ni reconstruye el índice
    dataset_features = valid_feats
    dataset_paths = valid_paths

_clean_dataset_and_index()


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path(__file__).parent / "sitios"
UPLOAD_DIR.mkdir(exist_ok=True)

# Mounting static directories
DATASET_ROOT = Path(__file__).parent / "sitios"       # ajusta si tus imágenes están en otra carpeta
UPLOAD_ROOT = UPLOAD_DIR

app.mount("/dataset", StaticFiles(directory=DATASET_ROOT), name="dataset")
app.mount("/sitios", StaticFiles(directory=UPLOAD_ROOT), name="sitios")



@app.post('/upload')
async def upload_image(file: UploadFile = File(...)):
    """
    Sube una imagen, la guarda en disco, extrae sus features y la agrega al índice FAISS.
    Persiste los features y rutas en el pickle.
    """
    try:
        global dataset_features, dataset_paths, index
        print(f"[UPLOAD DEBUG] Recibido archivo: {file.filename}")
        ext = Path(file.filename).suffix or '.jpg'
        image_id = str(uuid.uuid4())
        dest = UPLOAD_DIR / f"{image_id}{ext}"

        # Leer en memoria y normalizar a RGB + tamaño estándar antes de guardar
        contents = await file.read()
        print(f"[UPLOAD DEBUG] Tamaño archivo: {len(contents)} bytes")
        img = Image.open(BytesIO(contents)).convert('RGB')
        # Guardar la imagen en su tamaño original
        img.save(dest)
        print(f"[UPLOAD DEBUG] Guardado en: {dest}, existe: {dest.exists()}")


        # Verificar que el archivo se guardó
        if not dest.exists():
            print(f"[UPLOAD ERROR] Archivo NO se guardó en {dest}")
            raise Exception(f"Archivo no se guardó: {dest}")

        print(f"[UPLOAD DEBUG] Archivo verificado en disco")

        # Extraer features y agregar al índice FAISS
        # Extraer features con resize interno a 224x224 (no modifica el archivo guardado)
        feats_vec = extract_mixed_features(str(dest))
        feats = feats_vec.astype("float32")
        index.add(np.expand_dims(feats, axis=0))
        print(f"[UPLOAD DEBUG] Features extraídas y agregadas a FAISS")

        # Actualizar dataset en memoria (como lista)
        dataset_features.append(feats)
        rel_for_dataset = str(Path('sitios') / dest.name).replace('\\', '/')
        dataset_paths.append(rel_for_dataset)
        print(f"[UPLOAD DEBUG] Path relativo guardado: {rel_for_dataset}")
        print(f"[UPLOAD] Ruta absoluta guardada: {dest}")

        # Persistir cambios
        with open(Path(__file__).parent / "models/dataset_1_Layers_avg_pool.pkl", "wb") as f:
            pickle.dump({"features": np.array(dataset_features, dtype="float32"), "paths": dataset_paths}, f)
        faiss.write_index(index, str(INDEX_PATH))

        return JSONResponse({'id': image_id, 'filename': file.filename})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/search')
async def search_image(
    request: Request,
    file: UploadFile = File(...),
    radius: float = Form(None),
    k: int = Form(10)
):
    """
    Busca imágenes similares a la imagen recibida usando el índice FAISS.
    Devuelve una lista de resultados con url pública, id y distancia.
    """
    try:
        # Leer imagen en memoria (PIL) y extraer features directamente
        contents = await file.read()
        img = Image.open(BytesIO(contents))
        img = img.convert('RGB')  # mantener tamaño original; el extractor ya hace resize interno

        feats = extract_mixed_features(img)
        feats = np.array([feats]).astype("float32")

        # Buscar en FAISS
        distances, indices = index.search(feats, k)

        results = []
        base_url = str(request.base_url).rstrip('/')
        for dist, idx in zip(distances[0], indices[0]):
            if radius is None or dist <= radius:
                entry = dataset_paths[idx]
                rel_path = str(entry).replace("\\", "/")
                fname = Path(rel_path).name

                # DEBUG
                full_path = UPLOAD_DIR / fname
                exists = full_path.exists()
                print(f"[SEARCH DEBUG] idx={idx}, entry={entry}, fname={fname}, existe={exists}")
                if not exists:
                    print(f"[SEARCH SKIP] Omitiendo resultado porque falta archivo: {full_path}")
                    continue

                # Siempre servir desde /sitios usando solo el nombre de archivo
                url = f"{base_url}/sitios/{fname}"

                image_id = fname.split('.')[0]
                results.append({
                    "id": image_id,
                    "url": url,
                    "distance": float(dist)
                })

        return {"results": results}
    except Exception as e:
        import traceback
        print("\n========== [SEARCH ERROR] ==========")
        print(f"Archivo recibido: {getattr(file, 'filename', None)}")
        print(f"Request: {request.method} {request.url}")
        print(f"Error: {str(e)}")
        print("Traceback:")
        traceback.print_exc()
        print(f"dataset_features: {len(dataset_features) if 'dataset_features' in globals() else 'N/A'}")
        print(f"dataset_paths: {len(dataset_paths) if 'dataset_paths' in globals() else 'N/A'}")
        print(f"Index size: {index.ntotal if 'index' in globals() else 'N/A'}")
        print("====================================\n")
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/debug/files')
def debug_files():
    """
    Devuelve la lista de archivos presentes en la carpeta de imágenes para debug.
    """
    """Lista archivos en sitios/ para debug."""
    files = list(UPLOAD_DIR.glob('*'))
    return {
        "sitios_dir": str(UPLOAD_DIR),
        "exists": UPLOAD_DIR.exists(),
        "files": [f.name for f in files],
        "count": len(files)
    }




if __name__ == '__main__':
    import uvicorn
    # reload=False para evitar múltiples procesos y re-import pesado de TensorFlow
    uvicorn.run('main:app', host='0.0.0.0', port=8000, reload=False)
