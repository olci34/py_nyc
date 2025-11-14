import os
from contextlib import asynccontextmanager
from beanie import init_beanie
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from py_nyc.web.api.users_router import users_router
from py_nyc.web.api.listings_router import listings_router
from py_nyc.web.api.trips_router import trips_router
from py_nyc.web.api.cloudinary_router import cloudinary_router
from py_nyc.web.api.waitlist_router import waitlist_router
from py_nyc.web.api.feedback_router import feedback_router
from py_nyc.web.data_access.models.listing import Listing, Vehicle, Plate
from py_nyc.web.data_access.models.user import User
from py_nyc.web.data_access.models.waitlist import Waitlist
from py_nyc.web.data_access.models.feedback import Feedback
from py_nyc.web.dependencies import get_client, get_db
from py_nyc.web.core.config import get_settings

# Load environment-specific .env file
# Note: Settings class also loads the correct env file, but we load here too
# to ensure env vars are available as early as possible
# Set ENV variable to 'development', 'test', or 'production'
# Default to 'development' if not set (safest for local development)
env = os.getenv("ENV", "development")

# Production uses .env, others use .env.{environment}
if env == "production":
    env_file = ".env"
else:
    env_file = f".env.{env}"

load_dotenv(env_file, override=True)
print(f"🌍 Environment: {env}")
print(f"📁 Config file: {env_file} (loaded with override=True)")

# Get settings and parse CORS origins
settings = get_settings()
origins = settings.get_cors_origins_list()
print(f"🔒 CORS Origins: {origins}")

@asynccontextmanager
async def db_lifespan(app: FastAPI):
    db = await anext(get_db())
    
    try:
        # Test the connection
        ping_response = await db.command("ping")
        if int(ping_response["ok"]) != 1:
            raise Exception("Problem connecting to database.")
        print("Connected to database.")
        
        # Initialize Beanie
        await init_beanie(database=db, document_models=[Listing, Vehicle, Plate, User, Waitlist, Feedback])
        
        yield
    finally:
        # Close the client when the app shuts down
        client = get_client()
        client.close()

server = FastAPI(debug=True, lifespan=db_lifespan)

server.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Add routes
server.include_router(trips_router)
server.include_router(listings_router)
server.include_router(users_router)
server.include_router(cloudinary_router)
server.include_router(waitlist_router)
server.include_router(feedback_router)

if __name__ == '__main__':
    uvicorn.run(server, host='localhost', port=8000)
