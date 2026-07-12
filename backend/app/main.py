from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine
from app import models
from app.routers import auth

Base.metadata.create_all(bind=engine)

from app.routers import auth, departments, categories, employees, assets, allocations, transfers

app = FastAPI(
    title="AssetFlow API",
    description="Enterprise Asset & Resource Management System",
    version="1.0.0"
)

app.include_router(auth.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for hackathon dev simplicity, or keep specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(departments.router, prefix="/api/v1")
app.include_router(categories.router, prefix="/api/v1")
app.include_router(employees.router, prefix="/api/v1")
app.include_router(assets.router, prefix="/api/v1")
app.include_router(allocations.router, prefix="/api/v1")
app.include_router(transfers.router, prefix="/api/v1")


@app.get("/")
def root():
    return {
        "message": "Welcome to AssetFlow API",
        "status": "running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }