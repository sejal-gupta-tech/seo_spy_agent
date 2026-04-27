from motor.motor_asyncio import AsyncIOMotorClient
import os
from app.core.logger import logger

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")

class MongoDBManager:
    def __init__(self):
        self.client = None
        self.database = None

    async def connect(self):
        try:
            logger.info("Attempting MongoDB connection...")
            self.client = AsyncIOMotorClient(MONGO_URL, serverSelectionTimeoutMS=5000)
            self.database = self.client["seo_spy_db"]

            # Ping to verify connection
            await self.client.admin.command("ping")
            logger.info("MongoDB connected successfully")

        except Exception as e:
            logger.error(f"MongoDB connection failed: {e}")
            self.client = None
            self.database = None

    async def close(self):
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")

# Global instance
db_manager = MongoDBManager()
