from motor.motor_asyncio import AsyncIOMotorClient
from config import settings

client = None
database = None


async def connect_to_mongo():
    """Connect to MongoDB"""
    global client, database
    try:
        client = AsyncIOMotorClient(settings.MONGODB_URL)
        database = client[settings.DATABASE_NAME]
        
        # Test connection
        await client.admin.command('ping')
        print(f"✓ Connected to MongoDB: {settings.DATABASE_NAME}")
        
        # Verify collection exists and count documents
        collections = await database.list_collection_names()
        print(f"✓ Available collections: {collections}")
        
        if settings.QUESTIONS_COLLECTION in collections:
            count = await database[settings.QUESTIONS_COLLECTION].count_documents({})
            print(f"✓ Found {count} documents in {settings.QUESTIONS_COLLECTION} collection")
        else:
            print(f"⚠️ Collection '{settings.QUESTIONS_COLLECTION}' not found!")
            
    except Exception as e:
        print(f"✗ Failed to connect to MongoDB: {str(e)}")
        raise


async def close_mongo_connection():
    """Close MongoDB connection"""
    global client
    if client:
        client.close()
        print("Closed MongoDB connection")


def get_database():
    """Get database instance"""
    if database is None:
        raise RuntimeError("Database not connected. Call connect_to_mongo() first.")
    return database
