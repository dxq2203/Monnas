from typing import Union
from fastapi import FastAPI, Query
import requests
from api.v1.endpoints import power
from middleware.cors import setup_cors
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Create database...")
    try:
        yield
    finally:
        pass

app = FastAPI(lifespan=lifespan)

setup_cors(app)

app.include_router(power.router)



