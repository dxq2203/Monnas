from typing import Union
from fastapi import FastAPI, Query
import requests
from api.v1.endpoints import power, gameSession
from middleware.cors import setup_cors
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up...")
    # connect_to_mongo()
    try:
        yield
    finally:
        print("Shutting down...")
        # close_mongo_connection()

# app = FastAPI(lifespan=lifespan)
app = FastAPI()

setup_cors(app)

app.include_router(power.router)
app.include_router(gameSession.router)


