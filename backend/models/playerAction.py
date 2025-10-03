from models.main import MongoBaseModel


class PlayerActionModel(MongoBaseModel):
    turn_number: int
    class Config(MongoBaseModel.Config): 
        collection_name = "gameSession"