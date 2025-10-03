from pymongo.database import Database
from typing import List, Optional
from schemas.gameSession import GameSessionCreate, GameSession, GameSessionInDB, StageSnapshot
from services.main import AppCRUD # Giả sử AppCRUD được định nghĩa ở đây
from models.gameSession import GameSessionModel
from pydantic import ValidationError
from models.main import ObjectId

class GameSessionCRUD(AppCRUD):
    def create_game_session(self, game_session: GameSessionCreate) -> GameSessionInDB:
        # Chuyển đổi model create thành một dictionary để insert
        new_game_session_data = game_session.dict()
        
        # Thêm các trường mặc định nếu cần
        new_game_session_data.update({
            "end_time": None,
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
        for session in sessions:
            print("crud session", session)
        return [GameSessionInDB(**session) for session in sessions]
    
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
        # Tạo một dictionary để set các giá trị mới
        # Ví dụ: { "game_history.$[turn].stage_name": "new_stage_name" }
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
    
    def get_by_id(self, session_id: str) -> Optional[GameSessionInDB]:
        """
        Lấy một game session bằng ID của nó.
        Trả về None nếu không tìm thấy.
        """
        COLLECTION_NAME = GameSessionModel.Config.collection_name
        
        # MongoDB lưu _id dưới dạng ObjectId, không phải chuỗi (string)
        # Vì vậy, chúng ta cần chuyển đổi chuỗi ID nhận được thành ObjectId
        session_doc = self.db[COLLECTION_NAME].find_one({"_id": ObjectId(session_id)})
        
        if session_doc:
            # Nếu tìm thấy, parse nó thành Pydantic model và trả về
            return GameSessionInDB.parse_obj(session_doc)
            
        # Nếu không tìm thấy, trả về None
        return None