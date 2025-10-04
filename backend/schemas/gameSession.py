from pydantic import BaseModel, UUID4, Field
from datetime import datetime
from typing import Optional, Dict, Any, List
from models.main import PyObjectId, ObjectId


class PlayerActionBase(BaseModel):
    """
    Represents a single action taken by the player in a stage.
    Mô tả một hành động duy nhất mà người chơi thực hiện trong một giai đoạn.
    """
    player_action: Dict[str, Any] = Field(..., description="The player's action, e.g., 'BÓN PHÂN', 'TƯỚI NƯỚC' and its parameters.")

class StageResult(BaseModel):
    """
    Represents the calculated outcomes of a single stage.
    Mô tả kết quả được tính toán của một giai đoạn. Các giá trị này là *phát sinh trong giai đoạn*.
    """
    ch4_emission: float = Field(..., description="Methane (CH4) emitted in this stage (kg).")
    n2o_emission: float = Field(..., description="Nitrous Oxide (N2O) emitted in this stage (kg).")

class CumulativeState(BaseModel):
    """
    Represents the cumulative state of the game up to the end of a stage.
    Mô tả trạng thái tích lũy của game tính đến cuối một lượt.
    """
    cumulative_ch4_emission: float = Field(..., description="Total CH4 emission so far (kg).")
    cumulative_n2o_emission: float = Field(..., description="Total N2O emission so far (kg).")
    cumulative_emission: float = Field(..., description="Total GHG emission so far (kg CO2e).")

class StageSnapshot(BaseModel):
    """
    Represents a complete snapshot of a single stage's data.
    Mô tả một "bức ảnh" hoàn chỉnh về dữ liệu của một giai đoạn, dùng để lưu vào lịch sử.
    """
    stage_number: int = Field(..., gt=0, description="The sequential number of the stage (1, 2, 3, 4).")
    stage_name: str
    player_action: PlayerActionBase = Field(..., description="The action taken by the player in this stage.")
    weather_conditions: Dict[str, Any] = Field(..., description="Weather data used for calculations in this stage.")
    stage_result: StageResult = Field(..., description="The calculated results for this stage.")
    cumulative_state: CumulativeState = Field(..., description="The cumulative state of the game after this stage.")

# -----------------Game Session-------------------------
class GameSessionBase(BaseModel):
    """
    Represents a full game session, from start to finish.
    This is the main document that will be stored in the MongoDB collection.
    Mô tả toàn bộ một ván chơi. Đây là document chính sẽ được lưu trong collection của MongoDB.
    """
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    player_name: str = Field(default="Anonymous", description="Player's name (optional).")
    start_time: datetime = Field(default_factory=datetime.utcnow, description="Timestamp when the game started.")
    end_time: Optional[datetime] = Field(None, description="Timestamp when the game ended.")
    status: str = Field(default="in_progress", description="Current status of the game: 'in_progress', 'completed', 'failed'.")
    season_key: str = Field(default="dong-xuan", description="The key for the chosen season, e.g., 'dong-xuan'.")
    weather_data: Dict[str, Any] = Field(..., description="The full weather dataset for the entire season, fetched once at the start.")
    water_regime: str = Field(default="traditional_technique", description="Current status of the game: 'traditional_technique', 'awd', ...")     
    game_history: List[StageSnapshot] = Field(default=[], description="A list of snapshots for each completed turn.")
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
class GameSessionCreate(BaseModel):
    # Add fields required to create a game session
    player_name: str = Field(default="Anonymous", description="Player's name (optional).")
    start_time: datetime = Field(default_factory=datetime.utcnow, description="Timestamp when the game started.")
    status: str = Field(default="in_progress", description="Current status of the game: 'in_progress', 'completed', 'failed'.")    
    season_key: str = Field(default="dong-xuan", description="The key for the chosen season, e.g., 'dong-xuan'.")
    water_regime: str = Field(default="traditional_technique", description="Current status of the game: 'traditional_technique', 'awd', ...")    

# Properties to return to client
class GameSessionInDB(GameSessionBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
            ObjectId: str
        }
        orm_mode = True # Quan trọng để tương tác với đối tượng ORM-like

class GameSession(GameSessionInDB):
    """
    Model để trả về cho client, kế thừa từ GameSessionInDB.
    """    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
            ObjectId: str
        }
        orm_mode = True # Quan trọng để tương tác với đối tượng ORM-like
    
# Wrapper for returning a list of sessions
class GameSessionList(BaseModel):
    game_sessions: List[GameSessionInDB]
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
            ObjectId: str
        }
        orm_mode = True

# -----------------Player Action-------------------------
class PlayerActionCreate(PlayerActionBase):
    pass

class PlayerActionUpdate(BaseModel):
    action_type: str
    params: Dict[str, Any]

class PlayerActionInDB(PlayerActionBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        orm_mode = True

class PlayerAction(PlayerActionInDB):
    class Config: # Bắt buộc phải có Config để kế thừa đúng cách
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        orm_mode = True

# -----------------Turn Snapshot-------------------------
class StageSnapshotCreate(StageSnapshot):
    stage_number: int
    stage_name: str
    player_action: PlayerActionBase
    weather_conditions: Dict[str, Any]


