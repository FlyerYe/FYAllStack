from fastapi import FastAPI, Request
from app.api.tasks import router as tasks_router
from app.api.auth import router as auth_router
from app.api.categories import router as categories_router
from app.api.recipes import router as recipes_router
from app.api.upload import router as upload_router
from app.api.orders import admin_router as admin_orders_router
from app.api.orders import router as orders_router
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from app.exceptions import AppException
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

app = FastAPI()
app.include_router(tasks_router)
app.include_router(auth_router)
app.include_router(categories_router)
app.include_router(recipes_router)
app.include_router(upload_router)
app.include_router(orders_router)
app.include_router(admin_orders_router)

@app.get("/")
def root():
    return {
        "message": "server running"
    }

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory="app/uploads"), name="uploads")

@app.exception_handler(AppException)
async def app_exception_handler(
    request: Request,
    exc: AppException,
):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "message": exc.message,
        },
    )
