"""Vehicle catalogue routes.

Reading the catalogue requires a signed-in caller. Changing it - adding,
editing, deleting or restocking - requires an administrator.

Route order matters: "/search" is declared before "/{vehicle_id}", otherwise
the dynamic route matches first and the request is treated as a lookup for a
vehicle whose id is the literal string "search".
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from app.deps import (
    get_current_user,
    get_inventory_service,
    get_vehicle_service,
    require_admin,
)
from app.models import User
from app.schemas import (
    PurchaseRequest,
    PurchaseResponse,
    RestockRequest,
    RestockResponse,
    VehicleCreate,
    VehicleDetailResponse,
    VehicleListResponse,
    VehicleResponse,
    VehicleSearch,
    VehicleUpdate,
)
from app.services.inventory_service import InventoryService
from app.services.vehicle_service import VehicleService

router = APIRouter(prefix="/api/vehicles", tags=["vehicles"])


@router.post("", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
def create_vehicle(
    payload: VehicleCreate,
    service: VehicleService = Depends(get_vehicle_service),
    _: User = Depends(require_admin),
) -> VehicleResponse:
    """List a model, together with the cars it is stocked with. Admins only."""
    vehicle = service.create(
        make=payload.make,
        model=payload.model,
        category=payload.category,
        units=[unit.model_dump() for unit in payload.units],
    )
    return VehicleResponse(vehicle=vehicle)


@router.get("", response_model=VehicleListResponse)
def list_vehicles(
    service: VehicleService = Depends(get_vehicle_service),
    _: User = Depends(get_current_user),
) -> VehicleListResponse:
    """List every model, sold out or not, ordered by make then model."""
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


@router.get("/{vehicle_id}", response_model=VehicleDetailResponse)
def get_vehicle(
    vehicle_id: str,
    service: VehicleService = Depends(get_vehicle_service),
    _: User = Depends(get_current_user),
) -> VehicleDetailResponse:
    """Fetch one listing together with the individual cars behind it."""
    return VehicleDetailResponse(vehicle=service.get(vehicle_id))


@router.put("/{vehicle_id}", response_model=VehicleResponse)
def update_vehicle(
    vehicle_id: str,
    payload: VehicleUpdate,
    service: VehicleService = Depends(get_vehicle_service),
    _: User = Depends(require_admin),
) -> VehicleResponse:
    """Apply a partial update to a listing. Administrators only."""
    return VehicleResponse(vehicle=service.update(vehicle_id, payload.changes()))


@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vehicle(
    vehicle_id: str,
    service: VehicleService = Depends(get_vehicle_service),
    _: User = Depends(require_admin),
) -> Response:
    """Delete a listing and the cars it holds. Administrators only."""
    service.delete(vehicle_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{vehicle_id}/purchase", response_model=PurchaseResponse)
def purchase_vehicle(
    vehicle_id: str,
    payload: PurchaseRequest = PurchaseRequest(),
    service: InventoryService = Depends(get_inventory_service),
    _: User = Depends(get_current_user),
) -> PurchaseResponse:
    """Buy one car of this model: a named one, or the cheapest available."""
    vehicle, unit = service.purchase(vehicle_id, payload.unit_id)
    return PurchaseResponse(vehicle=vehicle, unit=unit)


@router.post("/{vehicle_id}/restock", response_model=RestockResponse)
def restock_vehicle(
    vehicle_id: str,
    payload: RestockRequest,
    service: InventoryService = Depends(get_inventory_service),
    _: User = Depends(require_admin),
) -> RestockResponse:
    """Take more cars of this model onto the lot. Administrators only."""
    vehicle, units = service.restock(
        vehicle_id, [unit.model_dump() for unit in payload.units]
    )
    return RestockResponse(vehicle=vehicle, restocked=len(units), units=units)
