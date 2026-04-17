from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(title="SEO Spy Agent")

app.include_router(router)
