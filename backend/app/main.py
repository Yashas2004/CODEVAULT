from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from . import models
from .database import engine
from .routers import users, snippets

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="CodeVault API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this in production
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(snippets.router)

@app.get("/")
def root():
    return {"status": "CodeVault API running"}