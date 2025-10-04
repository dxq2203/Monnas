from typing import List
from crud.gameSession import GameSessionCRUD
from schemas.gameSession import GameSession, GameSessionCreate, GameSessionInDB, StageSnapshotCreate, StageSnapshot, StageResult, CumulativeState, PlayerActionCreate
from services.main import AppService
from fastapi import HTTPException, status
from models.main import ObjectId
from services.game_engine import GameEngine, GameEngineError

class GameSessionService(AppService):
    def create_game_session(self, game_session: GameSessionCreate) -> GameSessionInDB:
        # Khởi tạo CRUD với database instance
        crud = GameSessionCRUD(self.db)
        created_session = crud.create_game_session(game_session)
        # Không cần from_orm nữa nếu CRUD trả về đúng model Pydantic
        return created_session

    def get_all_game_sessions(self) -> List[GameSessionInDB]:
        crud = GameSessionCRUD(self.db)
        sessions = crud.get_all_game_sessions()
        for session in sessions:
            print("service", session)
        return sessions
    
    def get_session_by_id(self, session_id: str) -> GameSessionInDB:
        """
        Lấy một game session bằng ID.
        Nếu không tìm thấy, sẽ raise lỗi HTTPException 404.
        """
        crud = GameSessionCRUD(self.db)
        
        session = crud.get_by_id(session_id)
        
        # Luồng xử lý lỗi: Nếu CRUD không trả về gì (None), tức là không tìm thấy
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Game session with ID '{session_id}' not found"
            )
            
        # Nếu tìm thấy, trả về session
        return session
    
    def play_stage(self, session_id: str, player_action_data: PlayerActionCreate) -> GameSession:
        """
        Xử lý logic cho một lượt chơi.
        """
        crud = GameSessionCRUD(self.db)

        # check invalid ObjectID
        if not ObjectId.is_valid(session_id):
            raise HTTPException(status_code=400, detail=f"Invalid session ID: {session_id}")
            
        current_session = crud.get_by_id(session_id)
        if not current_session:
            raise HTTPException(status_code=404, detail="GameSession not found")
        
        if current_session.status == "completed":
             raise HTTPException(status_code=400, detail="This game has already been completed.")

        current_stage_num = len(current_session.game_history) + 1
        season_key = current_session.season_key 

        weather_doc = self.db["weather_data"].find_one({"season_key": season_key})
        if not weather_doc or not weather_doc.get("data"):
            raise HTTPException(status_code=500, detail=f"Weather data for season '{season_key}' not found.")
        
        # access weather data
        try:
            weather_conditions = weather_doc["data"][current_stage_num - 1]
        except IndexError:
             raise HTTPException(status_code=500, detail=f"Weather data for stage {current_stage_num} not found.")

        try:
            game_engine = GameEngine(session=current_session)
            
            # play_stage của GameEngine sẽ thực hiện các bước 5, 6, 7, 8
            updated_session = game_engine.play_stage(
                player_actions=player_action_data, 
                weather_data=weather_conditions
            )
            
            saved_session = crud.update_session(updated_session)
            if not saved_session:
                raise HTTPException(status_code=500, detail="Failed to save the updated game session.")

            # 10. Trả về kết quả
            return saved_session

        except GameEngineError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
        
    def add_stage(self, session_id: str, stage_data: StageSnapshotCreate) -> GameSession:
        crud = GameSessionCRUD(self.db)
        
        # Logic nghiệp vụ: Lấy session hiện tại để tính toán
        current_session = crud.get_by_id(session_id) # Giả sử bạn có hàm get_by_id
        if not current_session:
             raise HTTPException(status_code=404, detail="GameSession not found")

        # --- LOGIC TÍNH TOÁN CỦA GAME ---
        ch4_emitted = 2.5 # (Tính toán dựa trên stage_data.player_action)
        n2o_emitted = 0.1 # (Tính toán)
        biomass_growth = 100.0 # (Tính toán)
            
        # Tạo StageResult
        stage_result = StageResult(ch4_emitted=ch4_emitted, n2o_emitted=n2o_emitted, biomass_growth=biomass_growth)

        # Lấy cumulative state của stage trước
        last_cumulative = CumulativeState(cumualative_ch4_emission=0, cumulative_n2o_emission=0, cumulative_biomass=0)
        if current_session.game_history:
            last_cumulative = current_session.game_history[-1].cumulative_state
        
        # Tính cumulative state mới
        new_cumulative_state = CumulativeState(
            cumualative_ch4_emission=last_cumulative.cumualative_ch4_emission + ch4_emitted,
            cumulative_n2o_emission=last_cumulative.cumulative_n2o_emission + n2o_emitted,
            cumulative_biomass=last_cumulative.cumulative_biomass + biomass_growth
        )

        # Tạo đối tượng StageSnapshot hoàn chỉnh để lưu vào DB
        full_stage_snapshot = StageSnapshot(
            stage_number=stage_data.stage_number,
            stage_name=stage_data.stage_name,
            player_action=stage_data.player_action,
            weather_conditions=stage_data.weather_conditions,
            stage_result=stage_result,
            cumulative_state=new_cumulative_state
        )
        
        updated_session = crud.add_stage_to_history(session_id, full_stage_snapshot)
        return updated_session

    def update_stage(self, session_id: str, stage_number: int, stage_update_data: dict) -> GameSession:
        crud = GameSessionCRUD(self.db)
        updated_session = crud.update_stage_in_history(session_id, stage_number, stage_update_data)
        if not updated_session:
            raise HTTPException(status_code=404, detail="GameSession or Stage not found")
        return updated_session
        
    def remove_stage(self, session_id: str, stage_number: int) -> GameSession:
        crud = GameSessionCRUD(self.db)
        updated_session = crud.remove_stage_from_history(session_id, stage_number)
        if not updated_session:
            raise HTTPException(status_code=404, detail="GameSession not found")
        return updated_session
    