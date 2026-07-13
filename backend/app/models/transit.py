from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Table, Text, Float
from sqlalchemy.orm import relationship as orm_relationship
from datetime import datetime, timezone
from backend.app.models.auth import Base

# Association table for TransitRoute and TransitStop M2M
class TransitRouteStop(Base):
    __tablename__ = "transit_route_stops"

    route_id = Column(Integer, ForeignKey("transit_routes.id", ondelete="CASCADE"), primary_key=True)
    stop_id = Column(Integer, ForeignKey("transit_stops.id", ondelete="CASCADE"), primary_key=True)
    stop_sequence = Column(Integer, nullable=False, default=1)
    is_deleted = Column(Boolean, default=False, nullable=False)
    version_id = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }

    route = orm_relationship("TransitRoute", back_populates="stops_association")
    stop = orm_relationship("TransitStop", back_populates="routes_association")



class TransitRoute(Base):
    __tablename__ = "transit_routes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    route_code = Column(String(50), unique=True, nullable=False, index=True)
    route_type = Column(String(50), nullable=False)  # Bus, Metro, LightRail, Shuttle
    status = Column(String(50), default="Active", nullable=False)  # Active, Delayed, Suspended
    description = Column(Text, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    version_id = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }

    stops_association = orm_relationship("TransitRouteStop", back_populates="route", cascade="all, delete-orphan")
    schedules = orm_relationship("TransitSchedule", back_populates="route", cascade="all, delete-orphan")
    shuttle_services = orm_relationship("ShuttleService", back_populates="route", cascade="all, delete-orphan")
    vehicle_assignments = orm_relationship("VehicleAssignment", back_populates="route", cascade="all, delete-orphan")
    incident_links = orm_relationship("TransitIncidentLink", back_populates="route", cascade="all, delete-orphan")


class TransitStop(Base):
    __tablename__ = "transit_stops"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    stop_code = Column(String(50), unique=True, nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    version_id = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }

    routes_association = orm_relationship("TransitRouteStop", back_populates="stop", cascade="all, delete-orphan")
    occupancies = orm_relationship("TransitOccupancy", back_populates="stop", cascade="all, delete-orphan")
    queues = orm_relationship("TransitQueue", back_populates="stop", cascade="all, delete-orphan")
    etas = orm_relationship("TransitETA", back_populates="stop", cascade="all, delete-orphan")


class TransitVehicle(Base):
    __tablename__ = "transit_vehicles"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_code = Column(String(50), unique=True, nullable=False, index=True)
    license_plate = Column(String(50), nullable=False)
    vehicle_type = Column(String(50), nullable=False)  # Bus, Train, Shuttle
    capacity = Column(Integer, nullable=False)
    status = Column(String(50), default="Active", nullable=False)  # Active, Maintenance, OutOfService

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    version_id = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }

    vehicle_assignments = orm_relationship("VehicleAssignment", back_populates="vehicle", cascade="all, delete-orphan")
    driver_assignments = orm_relationship("DriverAssignment", back_populates="vehicle", cascade="all, delete-orphan")
    trips = orm_relationship("TransitTrip", back_populates="vehicle", cascade="all, delete-orphan")
    telemetries = orm_relationship("TransitTelemetry", back_populates="vehicle", cascade="all, delete-orphan")
    capacities = orm_relationship("TransitCapacity", back_populates="vehicle", cascade="all, delete-orphan")
    occupancies = orm_relationship("TransitOccupancy", back_populates="vehicle", cascade="all, delete-orphan")


class Driver(Base):
    __tablename__ = "drivers"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    license_number = Column(String(100), unique=True, nullable=False, index=True)
    phone = Column(String(50), nullable=True)
    status = Column(String(50), default="Active", nullable=False)  # Active, OffDuty, Suspended

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    version_id = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }

    driver_assignments = orm_relationship("DriverAssignment", back_populates="driver", cascade="all, delete-orphan")
    trips = orm_relationship("TransitTrip", back_populates="driver", cascade="all, delete-orphan")


class Operator(Base):
    __tablename__ = "operators"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    contact_email = Column(String(100), nullable=False)
    phone = Column(String(50), nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    version_id = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }


class TransitHub(Base):
    __tablename__ = "transit_hubs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    location_zone = Column(String(100), nullable=False)
    capacity_status = Column(String(50), default="Normal", nullable=False)  # Normal, Crowded, Critical

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    version_id = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }


class ParkingZone(Base):
    __tablename__ = "parking_zones"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    total_spaces = Column(Integer, nullable=False)
    occupied_spaces = Column(Integer, nullable=False, default=0)
    location_zone = Column(String(50), nullable=False)
    status = Column(String(50), default="Open", nullable=False)  # Open, Closed, Full

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    version_id = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }


class ShuttleService(Base):
    __tablename__ = "shuttle_services"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    route_id = Column(Integer, ForeignKey("transit_routes.id", ondelete="CASCADE"), nullable=False, index=True)
    frequency_minutes = Column(Integer, nullable=False)
    operating_hours = Column(String(100), nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    version_id = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }

    route = orm_relationship("TransitRoute", back_populates="shuttle_services")


class VehicleAssignment(Base):
    __tablename__ = "vehicle_assignments"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("transit_vehicles.id", ondelete="CASCADE"), nullable=False, index=True)
    route_id = Column(Integer, ForeignKey("transit_routes.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(50), default="Active", nullable=False)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    version_id = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }

    vehicle = orm_relationship("TransitVehicle", back_populates="vehicle_assignments")
    route = orm_relationship("TransitRoute", back_populates="vehicle_assignments")


class DriverAssignment(Base):
    __tablename__ = "driver_assignments"

    id = Column(Integer, primary_key=True, index=True)
    driver_id = Column(Integer, ForeignKey("drivers.id", ondelete="CASCADE"), nullable=False, index=True)
    vehicle_id = Column(Integer, ForeignKey("transit_vehicles.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    status = Column(String(50), default="Active", nullable=False)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    version_id = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }

    driver = orm_relationship("Driver", back_populates="driver_assignments")
    vehicle = orm_relationship("TransitVehicle", back_populates="driver_assignments")


class TransitSchedule(Base):
    __tablename__ = "transit_schedules"

    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, ForeignKey("transit_routes.id", ondelete="CASCADE"), nullable=False, index=True)
    day_of_week = Column(Integer, nullable=False)  # 0 = Monday, 6 = Sunday
    departure_time = Column(String(5), nullable=False)  # HH:MM
    arrival_time = Column(String(5), nullable=False)  # HH:MM

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    version_id = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }

    route = orm_relationship("TransitRoute", back_populates="schedules")
    trips = orm_relationship("TransitTrip", back_populates="schedule", cascade="all, delete-orphan")


class TransitTrip(Base):
    __tablename__ = "transit_trips"

    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(Integer, ForeignKey("transit_schedules.id", ondelete="CASCADE"), nullable=False, index=True)
    vehicle_id = Column(Integer, ForeignKey("transit_vehicles.id", ondelete="CASCADE"), nullable=False, index=True)
    driver_id = Column(Integer, ForeignKey("drivers.id", ondelete="CASCADE"), nullable=False, index=True)
    actual_departure = Column(DateTime, nullable=True)
    actual_arrival = Column(DateTime, nullable=True)
    status = Column(String(50), default="Scheduled", nullable=False)  # Scheduled, InTransit, Completed, Cancelled

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    version_id = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }

    schedule = orm_relationship("TransitSchedule", back_populates="trips")
    vehicle = orm_relationship("TransitVehicle", back_populates="trips")
    driver = orm_relationship("Driver", back_populates="trips")
    delays = orm_relationship("TransitDelay", back_populates="trip", cascade="all, delete-orphan")
    etas = orm_relationship("TransitETA", back_populates="trip", cascade="all, delete-orphan")
    incident_links = orm_relationship("TransitIncidentLink", back_populates="trip", cascade="all, delete-orphan")


class TransitTelemetry(Base):
    __tablename__ = "transit_telemetry"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("transit_vehicles.id", ondelete="CASCADE"), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    speed = Column(Float, nullable=False)
    heading = Column(Float, nullable=False, default=0.0)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)

    vehicle = orm_relationship("TransitVehicle", back_populates="telemetries")



class TransitDelay(Base):
    __tablename__ = "transit_delays"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("transit_trips.id", ondelete="CASCADE"), nullable=False, index=True)
    delay_minutes = Column(Integer, nullable=False)
    reason = Column(Text, nullable=True)
    reported_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    version_id = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }

    trip = orm_relationship("TransitTrip", back_populates="delays")


class TransitCapacity(Base):
    __tablename__ = "transit_capacities"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("transit_vehicles.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    max_seats = Column(Integer, nullable=False)
    max_standing = Column(Integer, nullable=False)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    version_id = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }

    vehicle = orm_relationship("TransitVehicle", back_populates="capacities")


class TransitOccupancy(Base):
    __tablename__ = "transit_occupancies"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("transit_vehicles.id", ondelete="CASCADE"), nullable=False, index=True)
    stop_id = Column(Integer, ForeignKey("transit_stops.id", ondelete="CASCADE"), nullable=False, index=True)
    passenger_count = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    version_id = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }

    vehicle = orm_relationship("TransitVehicle", back_populates="occupancies")
    stop = orm_relationship("TransitStop", back_populates="occupancies")


class TransitQueue(Base):
    __tablename__ = "transit_queues"

    id = Column(Integer, primary_key=True, index=True)
    stop_id = Column(Integer, ForeignKey("transit_stops.id", ondelete="CASCADE"), nullable=False, index=True)
    queue_size = Column(Integer, nullable=False)
    average_wait_time_minutes = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    version_id = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }

    stop = orm_relationship("TransitStop", back_populates="queues")


class TransitETA(Base):
    __tablename__ = "transit_etas"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("transit_trips.id", ondelete="CASCADE"), nullable=False, index=True)
    stop_id = Column(Integer, ForeignKey("transit_stops.id", ondelete="CASCADE"), nullable=False, index=True)
    estimated_arrival = Column(DateTime, nullable=False)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    version_id = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }

    trip = orm_relationship("TransitTrip", back_populates="etas")
    stop = orm_relationship("TransitStop", back_populates="etas")


class TransitIncidentLink(Base):
    __tablename__ = "transit_incident_links"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    route_id = Column(Integer, ForeignKey("transit_routes.id", ondelete="CASCADE"), nullable=True, index=True)
    trip_id = Column(Integer, ForeignKey("transit_trips.id", ondelete="CASCADE"), nullable=True, index=True)
    status = Column(String(50), default="Active", nullable=False)  # Active, Resolved

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    version_id = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }

    route = orm_relationship("TransitRoute", back_populates="incident_links")
    trip = orm_relationship("TransitTrip", back_populates="incident_links")


class TransitAudit(Base):
    __tablename__ = "transit_audits"

    id = Column(Integer, primary_key=True, index=True)
    action = Column(String(100), nullable=False)
    actor_id = Column(Integer, nullable=True)
    target_type = Column(String(100), nullable=False)
    target_id = Column(Integer, nullable=True)
    changes = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    version_id = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }


class TransitAlert(Base):
    __tablename__ = "transit_alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_code = Column(String(100), unique=True, nullable=False, index=True)
    route_id = Column(Integer, ForeignKey("transit_routes.id", ondelete="CASCADE"), nullable=True, index=True)
    hub_id = Column(String(100), nullable=True, index=True)
    alert_type = Column(String(50), nullable=False)
    severity = Column(String(50), nullable=False)
    delay_minutes = Column(Integer, nullable=False, default=0)
    reason = Column(Text, nullable=True)
    estimated_resolution_time = Column(DateTime, nullable=True)
    reported_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    version_id = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }

    route = orm_relationship("TransitRoute")

