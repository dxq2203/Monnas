from pymongo.database import Database
from typing import List
from models.gameSession import GameSession
from schemas.gameSession import GameSessionCreate, GameSession
from services.main import AppCRUD
from uuid import uuid4

COLLECTION_NAME = "gameSession"

class GameSessionCRUD(AppCRUD):
    def create_game_session(self, game_session: GameSessionCreate) -> GameSession:
        new_game_session = GameSession(
            id=uuid4(),
            player_name=game_session.player_name,
            start_time=game_session.start_time,
            end_time=None,
            status=None,
            season_key=game_session.season_key,
            weather_data=[],
            game_history=[],
            final_metrics=None
        )
        result = self.db[COLLECTION_NAME].insert_one(new_game_session.dict())
        created_session = self.db[COLLECTION_NAME].find_one({"_id": result.inserted_id})
        return GameSession(**created_session)