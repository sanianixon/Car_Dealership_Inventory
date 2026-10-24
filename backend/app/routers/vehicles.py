"""Vehicle catalogue routes.

Every route here requires a signed-in caller. Deletion additionally requires
an administrator.
"""

from fastapi import APIRouter, Depends, status

from app.deps import get_current_user, get_vehicle_service
from app.models import User
from app.schemas import (
    VehicleCreate,
    VehicleListResponse,
    VehicleResponse,
)
from app.services.vehicle_service import VehicleService

router = APIRouter(prefix="/api/vehicles", tags=["vehicles"])


@router.post("", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
def create_vehicle(
    payload: VehicleCreate,
    service: VehicleService = Depends(get_vehicle_service),
    _: User = Depends(get_current_user),
) -> VehicleResponse:
    """Add a vehicle to the catalogue."""
    vehicle = service.create(
        make=payload.make,
        model=payload.model,
        category=payload.category,
        price=payload.price,
        quantity=payload.quantity,
    )
    return VehicleResponse(vehicle=vehicle)


@router.get("", response_model=VehicleListResponse)
def list_vehicles(
    service: VehicleService = Depends(get_vehicle_service),
    _: User = Depends(get_current_user),
) -> VehicleListResponse:
    """List every vehicle, sold out or not, ordered by make then model."""
    return VehicleListResponse(vehicles=service.list_all())


@router.get("/{vehicle_id}", response_model=VehicleResponse)
def get_vehicle(
    vehicle_id: str,
    service: VehicleService = Depends(get_vehicle_service),
    _: User = Depends(get_current_user),
) -> VehicleResponse:
    """Fetch one vehicle by id."""
    return VehicleResponse(vehicle=service.get(vehicle_id))
