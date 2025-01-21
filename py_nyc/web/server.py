from contextlib import asynccontextmanager
from beanie import init_beanie
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from py_nyc.web.api.listings_router import listings_router
from py_nyc.web.api.trips_router import trips_router
from fastapi.middleware.cors import CORSMiddleware
from py_nyc.web.core.listings_logic import ListingsLogic
from py_nyc.web.core.plates_logic import PlatesLogic
from py_nyc.web.core.trips_logic import TripsLogic
from py_nyc.web.core.vehicles_logic import VehiclesLogic
from py_nyc.web.data_access.models.listing import Listing, Plate, Vehicle
from py_nyc.web.data_access.services.listing_service import ListingService
from py_nyc.web.data_access.services.plate_service import PlateService
from py_nyc.web.data_access.services.trip_service import TripService
from motor.motor_asyncio import AsyncIOMotorClient

from py_nyc.web.data_access.services.vehicle_service import VehicleService

load_dotenv()

origins = [
    "http://localhost:3000",
    "http://localhost:8000",
    "https://tlc-shift.vercel.app",
    "https://tlc-shift-olci34s-projects.vercel.app"
]


async def setup_dependencies(app: FastAPI):
    print("Setup Dependencies")
    # Services
    listing_service = ListingService(app.database)
    vehicle_service = VehicleService(app.database)
    plate_service = PlateService(app.database)
    trips_service = TripService()
    # BLL
    listings_logic = ListingsLogic(listing_service)
    vehicles_logic = VehiclesLogic(vehicle_service)
    plates_logic = PlatesLogic(plate_service)
    trips_logic = TripsLogic(trips_service)
    # Attach to the app
    app.state.trips_logic = trips_logic
    app.state.listings_logic = listings_logic
    app.state.vehicles_logic = vehicles_logic
    app.state.plates_logic = plates_logic


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
    await init_beanie(database=app.database, document_models=[Listing, Vehicle, Plate])

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
server.include_router(listings_router)


if __name__ == '__main__':
    uvicorn.run(server, host='localhost', port=8000)
