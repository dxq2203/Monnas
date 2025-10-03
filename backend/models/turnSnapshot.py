from models.main import MongoBaseModel

# Model cụ thể của bạn kế thừa từ MongoBaseModel
class TurnSnapshotModel(MongoBaseModel):
    turn_number: int
    class Config(MongoBaseModel.Config): # Kế thừa Config của lớp cha
        collection_name = "gameSession"