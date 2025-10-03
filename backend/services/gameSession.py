from typing import List
from crud.gameSession import GameSessionCRUD
from schemas.gameSession import GameSession, GameSessionCreate, GameSessionInDB, StageSnapshotCreate, StageSnapshot, StageResult, CumulativeState
from services.main import AppService
from fastapi import HTTPException, status

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
    
    def add_turn(self, session_id: str, turn_data: StageSnapshotCreate) -> GameSession:
        crud = GameSessionCRUD(self.db)
        
        # Logic nghiệp vụ: Lấy session hiện tại để tính toán
        current_session = crud.get_by_id(session_id) # Giả sử bạn có hàm get_by_id
        if not current_session:
             raise HTTPException(status_code=404, detail="GameSession not found")

        # --- LOGIC TÍNH TOÁN CỦA GAME ---
        # Đây là nơi bạn tính toán turn_result và cumulative_state
        # Ví dụ đơn giản:
        ch4_emitted = 2.5 # (Tính toán dựa trên turn_data.player_action)
        n2o_emitted = 0.1 # (Tính toán)
        biomass_growth = 100.0 # (Tính toán)
        
        last_biomass = current_session.game_history[-1].cumulative_state.cumulative_biomass if current_session.game_history else 0
        new_cumulative_biomass = last_biomass + biomass_growth

        # Tạo đối tượng TurnSnapshot hoàn chỉnh để lưu vào DB
        full_turn_snapshot = StageSnapshot(
            **turn_data.dict(),
            turn_result=StageResult(ch4_emitted=ch4_emitted, n2o_emitted=n2o_emitted, biomass_growth=biomass_growth),
            cumulative_state=CumulativeState(cumulative_biomass=new_cumulative_biomass)
        )
        
        updated_session = crud.add_turn_to_history(session_id, full_turn_snapshot)
        return updated_session

    def update_turn(self, session_id: str, turn_number: int, turn_update_data: dict) -> GameSession:
        crud = GameSessionCRUD(self.db)
        updated_session = crud.update_turn_in_history(session_id, turn_number, turn_update_data)
        if not updated_session:
            raise HTTPException(status_code=404, detail="GameSession or Turn not found")
        return updated_session
        
    def remove_turn(self, session_id: str, turn_number: int) -> GameSession:
        crud = GameSessionCRUD(self.db)
        updated_session = crud.remove_turn_from_history(session_id, turn_number)
        if not updated_session:
            raise HTTPException(status_code=404, detail="GameSession not found")
        return updated_session
    