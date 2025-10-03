from typing import Union
from fastapi import FastAPI, Query
import requests
from api.v1.endpoints import power, gameSession, playerAction
from middleware.cors import setup_cors
from contextlib import asynccontextmanager
from db.db import db_client
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up...")
    # Ping to confirm a successful connection
    try:
        db_client.client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        print(e)
    
    yield
    
    print("Shutting down...")
    db_client.close()
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     print("Starting up...")
#     # connect_to_mongo()
#     try:
#         yield
#     finally:
#         pass
#         # close_mongo_connection()

# app = FastAPI(lifespan=lifespan)
app = FastAPI(lifespan=lifespan)

setup_cors(app)

app.include_router(power.router)
app.include_router(gameSession.router)
app.include_router(playerAction.router)


