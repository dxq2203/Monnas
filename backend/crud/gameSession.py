from pymongo.database import Database
from typing import List, Optional
from schemas.gameSession import GameSessionCreate, GameSession, GameSessionInDB, StageSnapshot
from services.main import AppCRUD # Giả sử AppCRUD được định nghĩa ở đây
from models.gameSession import GameSessionModel
from pydantic import ValidationError
from models.main import ObjectId
from config import GAME_CONFIG 

class GameSessionCRUD(AppCRUD):
    def create_game_session(self, game_session: GameSessionCreate) -> GameSessionInDB:
        # Chuyển đổi model create thành một dictionary để insert
        new_game_session_data = game_session.dict()
        print('New game session data to insert: ', new_game_session_data)
        weather_data = GAME_CONFIG['weather_data'][new_game_session_data['season_key']]
        print('Weather data for season:', weather_data)
        # Thêm các trường mặc định nếu cần
        new_game_session_data.update({
            "end_time": None,
            "weather_data": weather_data, 
            "game_history": [],
            "final_metrics": None
        })
        COLLECTION_NAME = GameSessionModel.Config.collection_name
        result = self.db[COLLECTION_NAME].insert_one(new_game_session_data)
        created_session = self.db[COLLECTION_NAME].find_one({"_id": result.inserted_id})
        return GameSessionInDB(**created_session)

    def get_all_game_sessions(self) -> List[GameSessionInDB]:
        COLLECTION_NAME = GameSessionModel.Config.collection_name
        sessions = list(self.db[COLLECTION_NAME].find())
        return [GameSessionInDB(**session) for session in sessions]
    
    
    def get_by_id(self, session_id: str) -> Optional[GameSessionInDB]:
        """
        Lấy một game session bằng ID của nó.
        Trả về None nếu không tìm thấy.
        """
        COLLECTION_NAME = GameSessionModel.Config.collection_name
        
        session_doc = self.db[COLLECTION_NAME].find_one({"_id": ObjectId(session_id)})
        
        if session_doc:
            return GameSessionInDB.parse_obj(session_doc)
            
        return None
    
    def update_session(self, session: GameSession) -> GameSessionInDB:
        """
        Cập nhật toàn bộ document game session sau khi đã được xử lý bởi Game Engine.
        Sử dụng replace_one để thay thế toàn bộ document.
        """
        COLLECTION_NAME = GameSessionModel.Config.collection_name
        
        # make sure _id be used
        session_data = session.dict(by_alias=True)

        result = self.db[COLLECTION_NAME].replace_one(
            {"_id": ObjectId(session.id)}, 
            session_data
        )

        updated_doc = self.db[COLLECTION_NAME].find_one({"_id": ObjectId(session.id)})
        
        if updated_doc:
            return GameSessionInDB.parse_obj(updated_doc)
        
        return None 
    
    def add_turn_to_history(self, session_id: str, turn: StageSnapshot) -> GameSessionInDB:
        """
        Thêm một TurnSnapshot vào mảng game_history của một GameSession.
        Sử dụng toán tử $push của MongoDB.
        """
        result = self.db["gameSession"].find_one_and_update(
            {"_id": ObjectId(session_id)},
            {"$push": {"game_history": turn.dict()}},
            return_document=True # Trả về document sau khi đã update
        )
        return GameSessionInDB.parse_obj(result)

    def update_turn_in_history(self, session_id: str, turn_number: int, turn_update_data: dict) -> GameSessionInDB:
        """
        Cập nhật một turn cụ thể trong mảng game_history.
        Sử dụng toán tử $set và arrayFilters.
        """
        update_fields = {f"game_history.$[turn].{key}": value for key, value in turn_update_data.items()}

        result = self.db["gameSession"].find_one_and_update(
            {"_id": ObjectId(session_id)},
            {"$set": update_fields},
            array_filters=[{"turn.turn_number": turn_number}],
            return_document=True
        )
        return GameSessionInDB.parse_obj(result)
        
    def remove_turn_from_history(self, session_id: str, turn_number: int) -> GameSessionInDB:
        """
        Xóa một turn khỏi mảng game_history.
        Sử dụng toán tử $pull của MongoDB.
        """
        result = self.db["gameSession"].find_one_and_update(
            {"_id": ObjectId(session_id)},
            {"$pull": {"game_history": {"turn_number": turn_number}}},
            return_document=True
        )
        return GameSessionInDB.parse_obj(result)
    