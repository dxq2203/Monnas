from typing import List
from crud.playerAction import PlayerActionCRUD
from schemas.gameSession import PlayerAction, PlayerActionBase, PlayerActionCreate, PlayerActionInDB, PlayerActionUpdate
from services.main import AppService
from fastapi import HTTPException, status

class PlayerActionService(AppService):
    def create_player_action(self, action_create: PlayerActionCreate):
        crud = PlayerActionCRUD(self.db)
        return crud.create(action_create)
    
    def get_all_player_actions(self) -> List[PlayerAction]:
        crud = PlayerActionCRUD(self.db)
        return crud.get_all()

    def get_player_action_by_id(self, action_id: str) -> PlayerAction:
        crud = PlayerActionCRUD(self.db)
        action = crud.get_by_id(action_id)
        if not action:
            # Logic nghiệp vụ: Nếu không tìm thấy, trả về lỗi 404
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player Action not found")
        return action

    def update_player_action(self, action_id: str, action_update: PlayerActionUpdate) -> PlayerAction:
        crud = PlayerActionCRUD(self.db)
        updated_action = crud.update(action_id, action_update)
        if not updated_action:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player Action not found")
        return updated_action

    def delete_player_action(self, action_id: str):
        crud = PlayerActionCRUD(self.db)
        success = crud.delete(action_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player Action not found")
        return {"detail": "Player Action deleted successfully"}