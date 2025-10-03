import os
from dotenv import load_dotenv
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from pymongo.database import Database
load_dotenv()

# uri = os.getenv("MONGO_URL") 
MONGODB_USER = os.getenv("MONGODB_USER")
MONGODB_PASSWORD = os.getenv("MONGODB_PASSWORD")
MONGODB_DB = os.getenv("MONGODB_DB")

uri = f"mongodb+srv://{MONGODB_USER}:{MONGODB_PASSWORD}@cluster0.olr4kkg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

def get_database() -> Database:
    # Provide the mongodb atlas url to connect python to mongodb using pymongo
 
   # Create the database for our example (we will use the same database throughout the tutorial
   # Send a ping to confirm a successful connection
   try:
      client.admin.command('ping')
      print("Pinged your deployment. You successfully connected to MongoDB!")
      yield client[MONGODB_DB]
   except Exception as e:
      print(e)