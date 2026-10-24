"""Vehicle catalogue routes.

Every route here requires a signed-in caller. Deletion additionally requires
an administrator.

Route order matters: "/search" is declared before "/{vehicle_id}", otherwise
the dynamic route matches first and the request is treated as a lookup for a
vehicle whose id is the literal string "search".
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from app.deps import get_current_user, get_vehicle_service, require_admin
from app.models import User
from app.schemas import (
    VehicleCreate,
    VehicleListResponse,
    VehicleResponse,
    VehicleSearch,
    VehicleUpdate,
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


@router.get("/search", response_model=VehicleListResponse)
def search_vehicles(
    filters: Annotated[VehicleSearch, Query()],
    service: VehicleService = Depends(get_vehicle_service),
    _: User = Depends(get_current_user),
) -> VehicleListResponse:
    """Search the catalogue by make, model, category and/or price range."""
    matches = service.search(
        make=filters.make,
        model=filters.model,
        category=filters.category,
        min_price=filters.min_price,
        max_price=filters.max_price,
    )
    return VehicleListResponse(vehicles=matches)


@router.get("/{vehicle_id}", response_model=VehicleResponse)
def get_vehicle(
    vehicle_id: str,
    service: VehicleService = Depends(get_vehicle_service),
    _: User = Depends(get_current_user),
) -> VehicleResponse:
    """Fetch one vehicle by id."""
    return VehicleResponse(vehicle=service.get(vehicle_id))


@router.put("/{vehicle_id}", response_model=VehicleResponse)
def update_vehicle(
    vehicle_id: str,
    payload: VehicleUpdate,
    service: VehicleService = Depends(get_vehicle_service),
    _: User = Depends(get_current_user),
) -> VehicleResponse:
    """Apply a partial update to a vehicle."""
    return VehicleResponse(vehicle=service.update(vehicle_id, payload.changes()))


@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vehicle(
    vehicle_id: str,
    service: VehicleService = Depends(get_vehicle_service),
    _: User = Depends(require_admin),
) -> Response:
    """Delete a vehicle. Administrators only."""
    service.delete(vehicle_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
