from pydantic import BaseModel, UUID4, Field
from datetime import datetime
from typing import Optional, Dict, Any, List
from utils.schema_helpers import PyObjectId, ObjectId


class PlayerAction(BaseModel):
    """
    Represents a single action taken by the player in a turn.
    Mô tả một hành động duy nhất mà người chơi thực hiện trong một lượt.
    """
    action_type: str
    params: Dict[str, Any]

class TurnResult(BaseModel):
    """
    Represents the calculated outcomes of a single turn.
    Mô tả kết quả được tính toán của một lượt chơi. Các giá trị này là *phát sinh trong lượt*.
    """
    ch4_emitted: float
    n2o_emitted: float
    biomass_growth: float

class CumulativeState(BaseModel):
    """
    Represents the cumulative state of the game up to the end of a turn.
    Mô tả trạng thái tích lũy của game tính đến cuối một lượt.
    """
    cummulative_biomass: float

class TurnSnapshot(BaseModel):
    """
    Represents a complete snapshot of a single turn's data.
    Mô tả một "bức ảnh" hoàn chỉnh về dữ liệu của một lượt chơi, dùng để lưu vào lịch sử.
    """
    turn_number: int
    stage_name: str
    player_action: PlayerAction
    weather_conditions: Dict[str, Any]
    turn_result: TurnResult
    cumulative_state: CumulativeState

class GameSession(BaseModel):
    """
    Represents a full game session, from start to finish.
    This is the main document that will be stored in the MongoDB collection.
    Mô tả toàn bộ một ván chơi. Đây là document chính sẽ được lưu trong collection của MongoDB.
    """
    id: UUID4
    player_name: str
    end_time: Optional[datetime] = None
    status: Optional[str] = None
    season_key: str
    weather_data: List[Dict[str, Any]]
    game_history: List[TurnSnapshot] = []
    final_metrics: Optional[Dict[str, Any]] = None

    class Config:
        """ Pydantic configuration. """
        allow_population_by_field_name = True
        arbitrary_types_allowed = True # Needed for PyObjectId
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
            ObjectId: str
        }

# Properties to receive on item creation
class GameSessionCreate(GameSession):
    # Add fields required to create a game session
    start_time: Optional[datetime] = None

# Properties to return to client
class GameSessionInDB(GameSessionCreate):
    id: str

    class Config:
        orm_mode = True

# Wrapper for returning a list of sessions
class GameSessionList(BaseModel):
    game_sessions: List[GameSessionInDB]