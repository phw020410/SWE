from fastapi import FastAPI

from app.routers import items

app = FastAPI(title="SWE FastAPI Demo", version="0.1.0")

app.include_router(items.router)


@app.get("/")
def root():
    return {"message": "Hello, FastAPI!"}


@app.get("/health")
def health():
    return {"status": "ok"}
