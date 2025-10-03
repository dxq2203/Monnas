from pymongo.database import Database
from typing import List
from crud import gameSession as crud_game_session
from schemas.gameSession import GameSessionCreate, GameSessionInDB

def create_game_session(db: Database, game_session: GameSessionCreate) -> GameSessionInDB:
    created_session = crud_game_session.create_game_session(db, game_session)
    return GameSessionInDB.from_orm(created_session)

def get_all_game_sessions(db: Database) -> List[GameSessionInDB]:
    sessions = crud_game_session.get_all_game_sessions(db)
    return [GameSessionInDB.from_orm(session) for session in sessions]