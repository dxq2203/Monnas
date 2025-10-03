from fastapi import APIRouter, Depends
# from db.db import get_database
from db.db import get_db as get_database
from schemas.gameSession import PlayerAction, PlayerActionBase, PlayerActionInDB, PlayerActionCreate, PlayerActionUpdate
from services.playerAction import PlayerActionService
from pymongo.database import Database
from typing import List
from fastapi import HTTPException, status

router = APIRouter(
    prefix="/player-action",
    tags=["Player Action"],
)

@router.post("/", response_model=PlayerAction, status_code=status.HTTP_201_CREATED)
def create_player_action(
    action: PlayerActionCreate,
    db: get_database = Depends()
):
    return PlayerActionService(db).create_player_action(action)

@router.get("/", response_model=List[PlayerAction])
def read_all_player_actions(db: get_database = Depends()):
    return PlayerActionService(db).get_all_player_actions()

@router.get("/{action_id}", response_model=PlayerAction)
def read_player_action(action_id: str, db: get_database = Depends()):
    return PlayerActionService(db).get_player_action_by_id(action_id)

@router.patch("/{action_id}", response_model=PlayerAction)
def update_player_action(
    action_id: str,
    action_update: PlayerActionUpdate,
    db: get_database = Depends()
):
    return PlayerActionService(db).update_player_action(action_id, action_update)

@router.delete("/{action_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_player_action(action_id: str, db: get_database = Depends()):
    PlayerActionService(db).delete_player_action(action_id)
    # Với 204 No Content, không trả về body
    return None