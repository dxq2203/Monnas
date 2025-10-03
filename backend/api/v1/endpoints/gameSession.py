from fastapi import FastAPI, APIRouter, Query, HTTPException, Depends
from fastapi.responses import JSONResponse
from utils.app_exceptions import AppExceptionCase
import requests

from db.db import get_database
from schemas.gameSession import GameSessionCreate, GameSessionInDB, GameSessionList
from services import gameSession as service_game_session
from pymongo.database import Database

router = APIRouter(
    prefix="/game-sessions",
    tags=["Game Sessions"],
)

@router.post("/", response_model=GameSessionInDB, status_code=201)
def create_game_session(
    game_session: GameSessionCreate,
    db: Database = Depends(get_database)
):
    """
    Create a new game session.
    """
    return service_game_session.create_game_session(db=db, game_session=game_session)

@router.get("/", response_model=GameSessionList)
def read_game_sessions(
    db: Database = Depends(get_database)
):
    """
    Retrieve all game sessions.
    """
    sessions = service_game_session.get_all_game_sessions(db=db)
    return {"game_sessions": sessions}