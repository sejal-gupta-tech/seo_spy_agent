import os
import re
import certifi
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import MONGO_URL, MONGODB_DB_NAME
from app.core.logger import logger


def _sanitize_mongo_url(uri: str) -> str:
    return re.sub(r"//([^/:@]+):([^@]+)@", "//***:***@", uri)


def _mongo_client_kwargs(uri: str) -> dict:
    kwargs = {
        "serverSelectionTimeoutMS": 10000,
        "connectTimeoutMS": 10000,
        "socketTimeoutMS": 20000,
    }
    lower_uri = uri.lower()
    if lower_uri.startswith("mongodb+srv://") or "tls=true" in lower_uri or "ssl=true" in lower_uri:
        kwargs["tls"] = True
        kwargs["tlsCAFile"] = certifi.where()
    return kwargs

class MongoDBManager:
    def __init__(self):
        self.client = None
        self.database = None
        self.last_error = None

    async def connect(self):
        try:
            if not MONGO_URL:
                self.last_error = "MONGO_URL is empty."
                logger.warning("MongoDB connection skipped because MONGO_URL is empty.")
                self.client = None
                self.database = None
                return

            safe_uri = _sanitize_mongo_url(MONGO_URL)
            logger.info(
                "Attempting MongoDB connection to %s using database '%s'...",
                safe_uri,
                MONGODB_DB_NAME,
            )

            self.client = AsyncIOMotorClient(
                MONGO_URL,
                **_mongo_client_kwargs(MONGO_URL),
            )
            self.database = self.client.get_default_database()
            if self.database is None:
                self.database = self.client[MONGODB_DB_NAME]

            # Ping to verify connection
            await self.client.admin.command("ping")
            self.last_error = None
            logger.info("MongoDB connected successfully")

        except Exception as e:
            self.last_error = str(e)
            error_message = str(e)
            logger.error("MongoDB connection failed: %s", error_message)
            if "SSL handshake failed" in error_message:
                logger.error(
                    "Atlas TLS handshake failed. This is usually a network or Atlas-side access issue, "
                    "not an application bug. Check Atlas Network Access, local firewall/VPN/TLS inspection, "
                    "or try a different network."
                )
            self.client = None
            self.database = None

    async def close(self):
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")
        self.client = None
        self.database = None

# Global instance
db_manager = MongoDBManager()
