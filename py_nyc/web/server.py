from contextlib import asynccontextmanager
from beanie import init_beanie
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from py_nyc.web.api.api import router as trips_router
from fastapi.middleware.cors import CORSMiddleware
from py_nyc.web.core.trips_logic import TripsLogic
from py_nyc.web.data_access.models.trip import Trip
from py_nyc.web.data_access.services.trip_service import TripService
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

origins = [
    "http://localhost:3000",
    "https://tlc-shift.vercel.app",
    "https://tlc-shift-olci34s-projects.vercel.app"
]


async def setup_dependencies(app: FastAPI):
    print("Setup Dependencies")
    # Services
    trips_service = TripService(app.database)
    # BLL
    trips_logic = TripsLogic(trips_service)
    # Attach to the app
    app.state.trips_logic = trips_logic


@asynccontextmanager
async def db_lifespan(app: FastAPI):
    app.mongodb_client = AsyncIOMotorClient("mongodb://localhost:27017")
    app.database = app.mongodb_client.get_database("tlc_shift")
    ping_response = await app.database.command("ping")
    if int(ping_response["ok"]) != 1:
        raise Exception("Problem connecting to database.")
    else:
        print("Connected to database.")

    await setup_dependencies(app)
    await init_beanie(database=app.database, document_models=[Trip])

    yield
    # Shutdown
    app.mongodb_client.close()


server = FastAPI(debug=True, lifespan=db_lifespan)

server.add_middleware(CORSMiddleware,
                      allow_origins=origins,
                      allow_credentials=True,
                      allow_methods=["*"],
                      allow_headers=["*"])


# Add routes and inject dependencies
server.include_router(trips_router)

if __name__ == '__main__':
    uvicorn.run(server, host='localhost', port=8000)
