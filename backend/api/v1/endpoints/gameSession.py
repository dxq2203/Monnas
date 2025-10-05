from fastapi import APIRouter, Depends
# from db.db import get_database
from db.db import get_db as get_database
from schemas.gameSession import GameSessionCreate, GameSessionInDB, GameSessionList, GameSession, StageSnapshotCreate, PlayerActionCreate
from services.gameSession import GameSessionService
from pymongo.database import Database
from typing import List
from fastapi import HTTPException, status

router = APIRouter(
    prefix="/game-sessions",
    tags=["Game Sessions"],
)

@router.post("/", response_model=GameSessionInDB, status_code=201)
def create_game_session(
    game_session: GameSessionCreate,
    db: get_database = Depends()
):
    """
    Create a new game session.
    """
    # import pdb; pdb.set_trace()
    return GameSessionService(db).create_game_session(game_session=game_session)

@router.get("/", response_model=GameSessionList)
def read_game_sessions(
    db: get_database = Depends()
):
    """
    Retrieve all game sessions.
    """
    # import pdb; pdb.set_trace()
    sessions = GameSessionService(db).get_all_game_sessions()
    return {"game_sessions": sessions}

@router.get("/{session_id}", response_model=GameSession)
def get_game_session_by_id(
    session_id: str,
    db: get_database = Depends()
):
    """
    Lấy thông tin chi tiết của một phiên game bằng ID của nó.
    """
    game_session = GameSessionService(db).get_session_by_id(session_id)
    return game_session

@router.post("/{session_id}/play-stage", response_model=GameSession)
def play_game_stage(
    session_id: str,
    player_action: PlayerActionCreate,
    db: get_database = Depends()
):
    """
    Thực hiện một lượt chơi cho giai đoạn hiện tại.
    
    Gửi hành động của người chơi. Backend sẽ tính toán kết quả,
    cập nhật trạng thái game và trả về session mới.
    """
    # import pdb; pdb.set_trace()
    service = GameSessionService(db)
    updated_session = service.play_stage(session_id, player_action)
    return updated_session

@router.post("/{session_id}/history", response_model=GameSession, status_code=status.HTTP_201_CREATED)
def add_new_stage_to_session(
    session_id: str,
    stage: StageSnapshotCreate,
    db: get_database = Depends()
):
    """
    Thêm một lượt chơi (stage) mới vào lịch sử của một game session.
    """
    return GameSessionService(db).add_stage(session_id, stage)

@router.patch("/{session_id}/history/{stage_number}", response_model=GameSession)
def update_existing_stage(
    session_id: str,
    stage_number: int,
    stage_update: dict, # Nhận một dict linh hoạt
    db: get_database = Depends()
):
    """
    Cập nhật một lượt chơi đã có trong lịch sử.
    Lưu ý: Chỉ gửi những trường cần thay đổi, ví dụ: { "stage_name": "Làm đòng" }
    """
    return GameSessionService(db).update_stage(session_id, stage_number, stage_update)

@router.delete("/{session_id}/history/{stage_number}", response_model=GameSession)
def remove_stage_from_session(
    session_id: str,
    stage_number: int,
    db: get_database = Depends()
):
    """
    Xóa một lượt chơi khỏi lịch sử của một game session.
    """
    return GameSessionService(db).remove_stage(session_id, stage_number)


