from functools import lru_cache
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Annotated
from fastapi import Depends

from py_nyc.web.core.users_logic import UsersLogic
from py_nyc.web.data_access.services.user_service import UserService

from .core.listings_logic import ListingsLogic
from .core.plates_logic import PlatesLogic
from .core.trips_logic import TripsLogic
from .core.vehicles_logic import VehiclesLogic
from .data_access.services.listing_service import ListingService
from .data_access.services.plate_service import PlateService
from .data_access.services.trip_service import TripService
from .data_access.services.vehicle_service import VehicleService

# Database dependency
@lru_cache()
def get_client() -> AsyncIOMotorClient:
    return AsyncIOMotorClient("mongodb://localhost:27017")

async def get_db():
    client = get_client()
    try:
      db = client.get_database("tlc_shift")
      yield db
    except Exception as e:
      print(f"Database error: {e}")
      raise

DB = Annotated[AsyncIOMotorClient, Depends(get_db)]

# Service layer dependencies
async def get_listing_service(db: DB) -> ListingService:
    return ListingService(db)

async def get_vehicle_service(db: DB) -> VehicleService:
    return VehicleService(db)

async def get_plate_service(db: DB) -> PlateService:
    return PlateService(db)

async def get_trip_service() -> TripService:
    return TripService()

async def get_user_service(db: DB) -> UserService:
    return UserService(db)

# Logic layer dependencies
async def get_listings_logic(
    listing_service: Annotated[ListingService, Depends(get_listing_service)]
) -> ListingsLogic:
    return ListingsLogic(listing_service)

async def get_vehicles_logic(
    vehicle_service: Annotated[VehicleService, Depends(get_vehicle_service)]
) -> VehiclesLogic:
    return VehiclesLogic(vehicle_service)

async def get_plates_logic(
    plate_service: Annotated[PlateService, Depends(get_plate_service)]
) -> PlatesLogic:
    return PlatesLogic(plate_service)

async def get_trips_logic(
    trip_service: Annotated[TripService, Depends(get_trip_service)]
) -> TripsLogic:
    return TripsLogic(trip_service)

async def get_users_logic(
    user_service: Annotated[UserService, Depends(get_user_service)]
) -> UsersLogic:
    return UsersLogic(user_service)

# Annotated types for cleaner dependency injection
ListingsLogicDep = Annotated[ListingsLogic, Depends(get_listings_logic)]
VehiclesLogicDep = Annotated[VehiclesLogic, Depends(get_vehicles_logic)]
PlatesLogicDep = Annotated[PlatesLogic, Depends(get_plates_logic)]
TripsLogicDep = Annotated[TripsLogic, Depends(get_trips_logic)]
UsersLogicDep = Annotated[UsersLogic, Depends(get_users_logic)] 