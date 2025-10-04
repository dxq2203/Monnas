# -*- coding: utf-8 -*-
"""
Pydantic Schemas for the Net-Zero Farmer Game.

This module defines the core data structures used throughout the application,
including the structure for game sessions, individual turns, and player actions.
These schemas are used for data validation, serialization, and database mapping.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId


class PlayerAction(BaseModel):
    """
    Represents a single action taken by the player in a stage.
    Mô tả một hành động duy nhất mà người chơi thực hiện trong một giai đoạn.
    """
    action_type: str = Field(..., description="The type of action, e.g., 'BÓN PHÂN', 'TƯỚI NƯỚC'.")
    params: Dict[str, Any] = Field(..., description="Parameters for the action, e.g., {'fertilizerType': 'urea', 'amountKg': 100}.")


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
    stage_name: str = Field(..., description="The name of the current growth stage, e.g., 'Gieo mạ'.")
    player_action: PlayerAction = Field(..., description="The action taken by the player in this stage.")
    weather_conditions: Dict[str, Any] = Field(..., description="Weather data used for calculations in this stage.")
    stage_result: StageResult = Field(..., description="The calculated results for this stage.")
    cumulative_state: CumulativeState = Field(..., description="The cumulative state of the game after this stage.")


# --- Main Schema ---

class GameSession(BaseModel):
    """
    Represents a full game session, from start to finish.
    This is the main document that will be stored in the MongoDB collection.
    Mô tả toàn bộ một ván chơi. Đây là document chính sẽ được lưu trong collection của MongoDB.
    """
    id: str = Field(..., alias="_id")
    player_name: str = Field(default="Anonymous", description="Player's name (optional).")
    
    start_time: datetime = Field(default_factory=datetime.utcnow, description="Timestamp when the game started.")
    end_time: Optional[datetime] = Field(None, description="Timestamp when the game ended.")
    
    status: str = Field(default="in_progress", description="Current status of the game: 'in_progress', 'completed', 'failed'.")
    
    season_key: str = Field(..., description="The key for the chosen season, e.g., 'dong-xuan'.")
    weather_data: Dict[str, Any] = Field(..., description="The full weather dataset for the entire season, fetched once at the start.")

    water_regime: str = Field(default="traditional_technique", description="Current status of the game: 'traditional_technique', 'awd', ...")

    game_history: List[StageSnapshot] = Field(default=[], description="A list of snapshots for each completed turn.")
    
    final_metrics: Optional[Dict[str, Any]] = Field(None, description="Final calculated score and metrics upon game completion.")

    class Config:
        """ Pydantic configuration. """
        validate_by_name = True
        arbitrary_types_allowed = True # Needed for PyObjectId
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
            ObjectId: str
        }
        json_schema_extra = {
            "example": {
                "_id": "64f8e...",
                "player_name": "Pro Farmer",
                "start_time": "2025-10-26T10:00:00Z",
                "status": "in_progress",
                "season_key": "dong-xuan",
                "weather_data": {"1": {"T2M": 30.1, "PRECTOTCORR": 5.2}, "2": {"T2M": 31.2, "PRECTOTCORR": 0.0}},
                "game_history": [
                    {
                        "turn_number": 1,
                        "stage_name": "Gieo mạ",
                        "player_action": {"action_type": "LÀM ĐẤT", "params": {}},
                        "weather_conditions": {"avg_temp": 30.5},
                        "turn_result": {"ch4_emitted": 2.5, "n2o_emitted": 0, "biomass_growth": 50.0},
                        "cumulative_state": {"cumulative_biomass": 50.0}
                    },
                    {
                        "turn_number": 2,
                        "stage_name": "Gieo mạ",
                        "player_action": {"action_type": "LÀM ĐẤT", "params": {}},
                        "weather_conditions": {"avg_temp": 30.5},
                        "turn_result": {"ch4_emitted": 2.5, "n2o_emitted": 0, "biomass_growth": 50.0},
                        "cumulative_state": {"cumulative_biomass": 50.0}
                    }
                ]
            }
        }