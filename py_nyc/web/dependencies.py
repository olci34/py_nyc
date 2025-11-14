from functools import lru_cache
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Annotated
from fastapi import Depends

from py_nyc.web.core.config import Settings, get_settings
from py_nyc.web.core.users_logic import UsersLogic
from py_nyc.web.data_access.services.user_service import UserService

from .core.listings_logic import ListingsLogic
from .core.plates_logic import PlatesLogic
from .core.trips_logic import TripsLogic
from .core.vehicles_logic import VehiclesLogic
from .core.waitlist_logic import WaitlistLogic
from .core.feedback_logic import FeedbackLogic
from .data_access.services.listing_service import ListingService
from .data_access.services.plate_service import PlateService
from .data_access.services.trip_service import TripService
from .data_access.services.vehicle_service import VehicleService
from .data_access.services.waitlist_service import WaitlistService
from .data_access.services.feedback_service import FeedbackService


# Database dependency


@lru_cache()
def get_client() -> AsyncIOMotorClient:
    settings = get_settings()
    return AsyncIOMotorClient(settings.mongodb_uri)


async def get_db():
    client = get_client()
    settings = get_settings()
    try:
        print(f"Database is connecting to {settings.mongodb_db_name}")
        db = client.get_database(settings.mongodb_db_name)
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


async def get_waitlist_service(db: DB) -> WaitlistService:
    return WaitlistService(db)


async def get_feedback_service(db: DB) -> FeedbackService:
    return FeedbackService(db)

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


async def get_waitlist_logic(
    waitlist_service: Annotated[WaitlistService, Depends(get_waitlist_service)]
) -> WaitlistLogic:
    return WaitlistLogic(waitlist_service)


async def get_feedback_logic(
    feedback_service: Annotated[FeedbackService, Depends(get_feedback_service)]
) -> FeedbackLogic:
    return FeedbackLogic(feedback_service)

# Annotated types for cleaner dependency injection
ListingsLogicDep = Annotated[ListingsLogic, Depends(get_listings_logic)]
VehiclesLogicDep = Annotated[VehiclesLogic, Depends(get_vehicles_logic)]
PlatesLogicDep = Annotated[PlatesLogic, Depends(get_plates_logic)]
TripsLogicDep = Annotated[TripsLogic, Depends(get_trips_logic)]
UsersLogicDep = Annotated[UsersLogic, Depends(get_users_logic)]
WaitlistLogicDep = Annotated[WaitlistLogic, Depends(get_waitlist_logic)]
FeedbackLogicDep = Annotated[FeedbackLogic, Depends(get_feedback_logic)]
