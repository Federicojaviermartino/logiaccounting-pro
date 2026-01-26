"""
Warehouse Service
Business logic for warehouses and locations
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID
import logging

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.inventory.warehouses.models import (
    Warehouse, WarehouseZone, WarehouseLocation,
    LocationTypeEnum, ZoneTypeEnum
)
from app.inventory.warehouses.schemas import (
    WarehouseCreate, WarehouseUpdate,
    ZoneCreate, ZoneUpdate,
    LocationCreate, LocationUpdate,
    BulkLocationCreate,
)

logger = logging.getLogger(__name__)


class WarehouseService:
    """Service for warehouse management."""

    def __init__(self, db: Session):
        self.db = db

    # ============== Warehouses ==============

    def create_warehouse(
        self,
        customer_id: UUID,
        data: WarehouseCreate,
        created_by: UUID = None,
    ) -> Warehouse:
        """Create a warehouse."""
        # Check for duplicate code
        existing = self.db.query(Warehouse).filter(
            Warehouse.customer_id == customer_id,
            Warehouse.code == data.code.upper()
        ).first()

        if existing:
            raise ValueError(f"Warehouse code '{data.code}' already exists")

        warehouse = Warehouse(
            customer_id=customer_id,
            code=data.code.upper(),
            name=data.name,
            phone=data.phone,
            email=data.email,
            manager_id=data.manager_id,
            allow_negative_stock=data.allow_negative_stock,
            inventory_account_id=data.inventory_account_id,
            adjustment_account_id=data.adjustment_account_id,
            created_by=created_by,
        )

        # Address
        if data.address:
            warehouse.address_line1 = data.address.line1
            warehouse.address_line2 = data.address.line2
            warehouse.city = data.address.city
            warehouse.state = data.address.state
            warehouse.postal_code = data.address.postal_code
            warehouse.country = data.address.country

        # Coordinates
        if data.coordinates:
            warehouse.latitude = data.coordinates.latitude
            warehouse.longitude = data.coordinates.longitude

        self.db.add(warehouse)
        self.db.commit()
        self.db.refresh(warehouse)

        # Create default zones
        self._create_default_zones(warehouse.id)

        # Create default input/output locations
        self._create_default_locations(warehouse.id)

        logger.info(f"Created warehouse: {warehouse.code}")
        return warehouse

    def _create_default_zones(self, warehouse_id: UUID):
        """Create default zones for a warehouse."""
        default_zones = [
            ("RCV", "Receiving", ZoneTypeEnum.RECEIVING.value, 1),
            ("STG", "Storage", ZoneTypeEnum.STORAGE.value, 2),
            ("PCK", "Picking", ZoneTypeEnum.PICKING.value, 3),
            ("SHP", "Shipping", ZoneTypeEnum.SHIPPING.value, 4),
        ]

        for code, name, zone_type, seq in default_zones:
            zone = WarehouseZone(
                warehouse_id=warehouse_id,
                code=code,
                name=name,
                zone_type=zone_type,
                sequence=seq,
            )
            self.db.add(zone)

        self.db.commit()

    def _create_default_locations(self, warehouse_id: UUID):
        """Create default special locations."""
        warehouse = self.db.query(Warehouse).get(warehouse_id)

        # Get receiving zone
        rcv_zone = self.db.query(WarehouseZone).filter(
            WarehouseZone.warehouse_id == warehouse_id,
            WarehouseZone.code == "RCV"
        ).first()

        # Get shipping zone
        shp_zone = self.db.query(WarehouseZone).filter(
            WarehouseZone.warehouse_id == warehouse_id,
            WarehouseZone.code == "SHP"
        ).first()

        # Input location (receiving)
        input_loc = WarehouseLocation(
            warehouse_id=warehouse_id,
            zone_id=rcv_zone.id if rcv_zone else None,
            code="INPUT",
            name="Receiving Input",
            location_type=LocationTypeEnum.INTERNAL.value,
            is_pickable=False,
            is_receivable=True,
        )
        self.db.add(input_loc)

        # Output location (shipping)
        output_loc = WarehouseLocation(
            warehouse_id=warehouse_id,
            zone_id=shp_zone.id if shp_zone else None,
            code="OUTPUT",
            name="Shipping Output",
            location_type=LocationTypeEnum.INTERNAL.value,
            is_pickable=True,
            is_receivable=False,
        )
        self.db.add(output_loc)

        # Adjustment location
        adj_loc = WarehouseLocation(
            warehouse_id=warehouse_id,
            code="ADJUSTMENT",
            name="Inventory Adjustment",
            location_type=LocationTypeEnum.ADJUSTMENT.value,
            is_pickable=False,
            is_receivable=False,
        )
        self.db.add(adj_loc)

        # Scrap location
        scrap_loc = WarehouseLocation(
            warehouse_id=warehouse_id,
            code="SCRAP",
            name="Scrap / Waste",
            location_type=LocationTypeEnum.SCRAP.value,
            is_scrap_location=True,
            is_pickable=False,
            is_receivable=True,
        )
        self.db.add(scrap_loc)

        self.db.commit()

    def get_warehouse_by_id(self, warehouse_id: UUID) -> Optional[Warehouse]:
        """Get warehouse by ID."""
        return self.db.query(Warehouse).options(
            joinedload(Warehouse.zones),
        ).get(warehouse_id)

    def get_warehouse_by_code(
        self,
        customer_id: UUID,
        code: str
    ) -> Optional[Warehouse]:
        """Get warehouse by code."""
        return self.db.query(Warehouse).filter(
            Warehouse.customer_id == customer_id,
            Warehouse.code == code.upper()
        ).first()

    def get_warehouses(
        self,
        customer_id: UUID,
        active_only: bool = True,
    ) -> List[Warehouse]:
        """Get all warehouses for a customer."""
        query = self.db.query(Warehouse).filter(
            Warehouse.customer_id == customer_id
        )

        if active_only:
            query = query.filter(Warehouse.is_active == True)

        return query.options(
            joinedload(Warehouse.zones)
        ).order_by(Warehouse.code).all()

    def update_warehouse(
        self,
        warehouse_id: UUID,
        data: WarehouseUpdate,
    ) -> Warehouse:
        """Update a warehouse."""
        warehouse = self.get_warehouse_by_id(warehouse_id)
        if not warehouse:
            raise ValueError("Warehouse not found")

        update_data = data.dict(exclude_unset=True)

        # Handle address
        if "address" in update_data and update_data["address"]:
            addr = update_data.pop("address")
            warehouse.address_line1 = addr.get("line1")
            warehouse.address_line2 = addr.get("line2")
            warehouse.city = addr.get("city")
            warehouse.state = addr.get("state")
            warehouse.postal_code = addr.get("postal_code")
            warehouse.country = addr.get("country")

        # Handle coordinates
        if "coordinates" in update_data and update_data["coordinates"]:
            coords = update_data.pop("coordinates")
            warehouse.latitude = coords.get("latitude")
            warehouse.longitude = coords.get("longitude")

        for key, value in update_data.items():
            if hasattr(warehouse, key):
                setattr(warehouse, key, value)

        self.db.commit()
        self.db.refresh(warehouse)

        return warehouse

    # ============== Zones ==============

    def create_zone(
        self,
        warehouse_id: UUID,
        data: ZoneCreate,
    ) -> WarehouseZone:
        """Create a zone in a warehouse."""
        # Check for duplicate code
        existing = self.db.query(WarehouseZone).filter(
            WarehouseZone.warehouse_id == warehouse_id,
            WarehouseZone.code == data.code.upper()
        ).first()

        if existing:
            raise ValueError(f"Zone code '{data.code}' already exists in this warehouse")

        zone = WarehouseZone(
            warehouse_id=warehouse_id,
            code=data.code.upper(),
            name=data.name,
            zone_type=data.zone_type.value if data.zone_type else None,
            description=data.description,
            sequence=data.sequence,
        )

        self.db.add(zone)
        self.db.commit()
        self.db.refresh(zone)

        return zone

    def get_zones(
        self,
        warehouse_id: UUID,
        active_only: bool = True,
    ) -> List[WarehouseZone]:
        """Get zones for a warehouse."""
        query = self.db.query(WarehouseZone).filter(
            WarehouseZone.warehouse_id == warehouse_id
        )

        if active_only:
            query = query.filter(WarehouseZone.is_active == True)

        return query.order_by(WarehouseZone.sequence, WarehouseZone.code).all()

    def update_zone(
        self,
        zone_id: UUID,
        data: ZoneUpdate,
    ) -> WarehouseZone:
        """Update a zone."""
        zone = self.db.query(WarehouseZone).get(zone_id)
        if not zone:
            raise ValueError("Zone not found")

        for key, value in data.dict(exclude_unset=True).items():
            if value is not None:
                if key == "zone_type":
                    value = value.value
                setattr(zone, key, value)

        self.db.commit()
        self.db.refresh(zone)

        return zone

    # ============== Locations ==============

    def create_location(
        self,
        warehouse_id: UUID,
        data: LocationCreate,
    ) -> WarehouseLocation:
        """Create a location in a warehouse."""
        # Check for duplicate code
        existing = self.db.query(WarehouseLocation).filter(
            WarehouseLocation.warehouse_id == warehouse_id,
            WarehouseLocation.code == data.code.upper()
        ).first()

        if existing:
            raise ValueError(f"Location code '{data.code}' already exists in this warehouse")

        # Calculate level and path
        level = 0
        path = "/"

        if data.parent_id:
            parent = self.db.query(WarehouseLocation).get(data.parent_id)
            if parent:
                level = parent.level + 1
                path = f"{parent.path}{parent.id}/"

        location = WarehouseLocation(
            warehouse_id=warehouse_id,
            zone_id=data.zone_id,
            parent_id=data.parent_id,
            code=data.code.upper(),
            name=data.name,
            barcode=data.barcode,
            location_type=data.location_type.value,
            is_scrap_location=data.is_scrap_location,
            is_return_location=data.is_return_location,
            is_pickable=data.is_pickable,
            is_receivable=data.is_receivable,
            level=level,
            path=path,
        )

        # Capacity
        if data.capacity:
            location.max_weight = data.capacity.max_weight
            location.max_volume = data.capacity.max_volume
            location.max_items = data.capacity.max_items

        self.db.add(location)
        self.db.commit()
        self.db.refresh(location)

        return location

    def get_location_by_id(self, location_id: UUID) -> Optional[WarehouseLocation]:
        """Get location by ID."""
        return self.db.query(WarehouseLocation).options(
            joinedload(WarehouseLocation.zone)
        ).get(location_id)

    def get_location_by_code(
        self,
        warehouse_id: UUID,
        code: str
    ) -> Optional[WarehouseLocation]:
        """Get location by code."""
        return self.db.query(WarehouseLocation).filter(
            WarehouseLocation.warehouse_id == warehouse_id,
            WarehouseLocation.code == code.upper()
        ).first()

    def get_location_by_barcode(
        self,
        customer_id: UUID,
        barcode: str
    ) -> Optional[WarehouseLocation]:
        """Get location by barcode (across all warehouses)."""
        return self.db.query(WarehouseLocation).join(Warehouse).filter(
            Warehouse.customer_id == customer_id,
            WarehouseLocation.barcode == barcode
        ).first()

    def get_locations(
        self,
        warehouse_id: UUID,
        zone_id: UUID = None,
        location_type: str = None,
        active_only: bool = True,
        page: int = 1,
        page_size: int = 100,
    ) -> Tuple[List[WarehouseLocation], int]:
        """Get locations for a warehouse."""
        query = self.db.query(WarehouseLocation).filter(
            WarehouseLocation.warehouse_id == warehouse_id
        )

        if active_only:
            query = query.filter(WarehouseLocation.is_active == True)

        if zone_id:
            query = query.filter(WarehouseLocation.zone_id == zone_id)

        if location_type:
            query = query.filter(WarehouseLocation.location_type == location_type)

        total = query.count()

        locations = query.options(
            joinedload(WarehouseLocation.zone)
        ).order_by(
            WarehouseLocation.code
        ).offset((page - 1) * page_size).limit(page_size).all()

        return locations, total

    def get_pickable_locations(
        self,
        warehouse_id: UUID,
    ) -> List[WarehouseLocation]:
        """Get locations that can be picked from."""
        return self.db.query(WarehouseLocation).filter(
            WarehouseLocation.warehouse_id == warehouse_id,
            WarehouseLocation.is_active == True,
            WarehouseLocation.is_pickable == True,
            WarehouseLocation.location_type == LocationTypeEnum.INTERNAL.value,
        ).order_by(WarehouseLocation.code).all()

    def get_receivable_locations(
        self,
        warehouse_id: UUID,
    ) -> List[WarehouseLocation]:
        """Get locations that can receive stock."""
        return self.db.query(WarehouseLocation).filter(
            WarehouseLocation.warehouse_id == warehouse_id,
            WarehouseLocation.is_active == True,
            WarehouseLocation.is_receivable == True,
        ).order_by(WarehouseLocation.code).all()

    def update_location(
        self,
        location_id: UUID,
        data: LocationUpdate,
    ) -> WarehouseLocation:
        """Update a location."""
        location = self.get_location_by_id(location_id)
        if not location:
            raise ValueError("Location not found")

        update_data = data.dict(exclude_unset=True)

        # Handle capacity
        if "capacity" in update_data and update_data["capacity"]:
            cap = update_data.pop("capacity")
            location.max_weight = cap.get("max_weight")
            location.max_volume = cap.get("max_volume")
            location.max_items = cap.get("max_items")

        for key, value in update_data.items():
            if hasattr(location, key):
                setattr(location, key, value)

        self.db.commit()
        self.db.refresh(location)

        return location

    def bulk_create_locations(
        self,
        warehouse_id: UUID,
        data: BulkLocationCreate,
    ) -> dict:
        """Create multiple locations from a pattern."""
        created = 0
        skipped = 0
        errors = []

        for aisle_num in range(1, data.aisle_count + 1):
            aisle = f"{data.aisle_prefix}{aisle_num:02d}" if data.aisle_count > 1 else data.aisle_prefix

            for rack in range(1, data.rack_count + 1):
                for level in range(1, data.level_count + 1):
                    for bin_num in range(1, data.bin_count + 1):
                        try:
                            code = data.code_format.format(
                                aisle=aisle,
                                rack=rack,
                                level=level,
                                bin=bin_num,
                            )

                            # Check if exists
                            existing = self.get_location_by_code(warehouse_id, code)
                            if existing:
                                skipped += 1
                                continue

                            location = WarehouseLocation(
                                warehouse_id=warehouse_id,
                                zone_id=data.zone_id,
                                code=code.upper(),
                                name=code,
                                location_type=LocationTypeEnum.INTERNAL.value,
                            )

                            if data.capacity:
                                location.max_weight = data.capacity.max_weight
                                location.max_volume = data.capacity.max_volume
                                location.max_items = data.capacity.max_items

                            self.db.add(location)
                            created += 1

                        except Exception as e:
                            errors.append({"code": code, "error": str(e)})

        self.db.commit()

        return {
            "created": created,
            "skipped": skipped,
            "errors": errors,
        }


def get_warehouse_service(db: Session) -> WarehouseService:
    """Factory function."""
    return WarehouseService(db)
