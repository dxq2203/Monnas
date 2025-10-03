from pymongo.database import Database

class DBSessionContext:
    def __init__(self, db: Database):
        self.db = db

class AppService(DBSessionContext):
    pass

class AppCRUD(DBSessionContext):
    pass
