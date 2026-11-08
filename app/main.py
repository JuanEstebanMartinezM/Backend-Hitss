from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routes.alarms import router as alarms_router

# Crear las tablas en la base de datos SQLite si no existen
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="API de Gestión de Alarmas y Criticidad",
    description="Backend en Python + FastAPI para la prueba técnica Full Stack. Desacoplado y con arquitectura REST.",
    version="1.0.0"
)

# Configuración de CORS para permitir la comunicación fluida con el frontend React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar rutas
app.include_router(alarms_router)

@app.get("/", tags=["Health"])
def health_check():
    return {
        "status": "online",
        "service": "API de Gestión de Alarmas",
        "version": "1.0.0",
        "docs": "/docs"
    }

