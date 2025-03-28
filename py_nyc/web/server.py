from contextlib import asynccontextmanager
from beanie import init_beanie
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from py_nyc.web.api.users_router import users_router
from py_nyc.web.api.listings_router import listings_router
from py_nyc.web.api.trips_router import trips_router
from py_nyc.web.data_access.models.listing import Listing, Vehicle, Plate
from py_nyc.web.data_access.models.user import User
from py_nyc.web.dependencies import get_client, get_db

load_dotenv()

origins = [
    "http://localhost:3000",
    "http://localhost:8000",
    "https://tlc-shift.vercel.app",
    "https://tlc-shift-olci34s-projects.vercel.app"
]

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
        await init_beanie(database=db, document_models=[Listing, Vehicle, Plate, User])
        
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

if __name__ == '__main__':
    uvicorn.run(server, host='localhost', port=8000)
