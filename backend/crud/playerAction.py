from services.main import AppCRUD
from schemas.gameSession import PlayerActionBase, PlayerAction, PlayerActionCreate, PlayerActionUpdate, PlayerActionInDB
from models.playerAction import PlayerActionModel
from typing import Optional, List
from models.main import ObjectId

COLLECTION_NAME = PlayerActionModel.Config.collection_name

class PlayerActionCRUD(AppCRUD):
    def create(self, action: PlayerActionCreate) -> PlayerActionInDB:
        """Tạo một action mới."""
        action_data = action.dict()
        result = self.db[COLLECTION_NAME].insert_one(action_data)
        created_action = self.db[COLLECTION_NAME].find_one({"_id": result.inserted_id})
        return PlayerActionInDB.parse_obj(created_action)

    def get_by_id(self, action_id: str) -> Optional[PlayerActionInDB]:
        """Lấy một action bằng ID."""
        action = self.db[COLLECTION_NAME].find_one({"_id": ObjectId(action_id)})
        if action:
            return PlayerActionInDB.parse_obj(action)
        return None

    def get_all(self) -> List[PlayerActionInDB]:
        """Lấy tất cả các action."""
        actions_cursor = list(self.db[COLLECTION_NAME].find())
        return [PlayerActionInDB.parse_obj(action) for action in actions_cursor]

    def update(self, action_id: str, action_update: PlayerActionUpdate) -> Optional[PlayerActionInDB]:
        """Cập nhật một action."""
        # exclude_unset=True rất quan trọng: chỉ cập nhật những trường được gửi lên
        update_data = action_update.dict(exclude_unset=True)
        
        if not update_data:
            # Nếu không có gì để cập nhật, trả về action hiện tại
            return self.get_by_id(action_id)

        result = self.db[COLLECTION_NAME].find_one_and_update(
            {"_id": ObjectId(action_id)},
            {"$set": update_data},
            return_document=True # Trả về document sau khi đã update
        )
        if result:
            return PlayerActionInDB.parse_obj(result)
        return None

    def delete(self, action_id: str) -> bool:
        """Xóa một action."""
        result = self.db[COLLECTION_NAME].delete_one({"_id": ObjectId(action_id)})
        return result.deleted_count > 0
