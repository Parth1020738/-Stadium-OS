from fastapi import HTTPException

class CrowdValidationError(Exception):
    def __init__(self, errors: dict[str, str]):
        super().__init__(str(errors))
        self.errors = errors

class CrowdValidator:
    @staticmethod
    def validate_zone(name: str, max_capacity: int, safe_capacity_limit: int) -> None:
        errors = {}
        if not name or not name.strip():
            errors["name"] = "Zone name is required"
        
        if max_capacity <= 0:
            errors["max_capacity"] = "Max capacity must be greater than zero"
        if safe_capacity_limit <= 0:
            errors["safe_capacity_limit"] = "Safe capacity limit must be greater than zero"
        elif safe_capacity_limit > max_capacity:
            errors["safe_capacity_limit"] = "Safe capacity limit cannot exceed max capacity"

        if errors:
            raise CrowdValidationError(errors)

    @staticmethod
    def validate_camera(device_id: str, name: str, status: str) -> None:
        errors = {}
        if not device_id or not device_id.strip():
            errors["device_id"] = "Device ID is required"
        if not name or not name.strip():
            errors["name"] = "Camera name is required"
        if status not in {"Active", "Offline", "Maintenance"}:
            errors["status"] = "Invalid camera status. Must be Active, Offline, or Maintenance"

        if errors:
            raise CrowdValidationError(errors)

    @staticmethod
    def validate_density(density_level: float) -> None:
        if density_level < 0.0:
            raise CrowdValidationError({"density_level": "Density level cannot be negative"})

    @staticmethod
    def validate_occupancy(occupancy_count: int, capacity_utilization_ratio: float) -> None:
        errors = {}
        if occupancy_count < 0:
            errors["occupancy_count"] = "Occupancy count cannot be negative"
        if capacity_utilization_ratio < 0.0:
            errors["capacity_utilization_ratio"] = "Capacity utilization ratio cannot be negative"

        if errors:
            raise CrowdValidationError(errors)

    @staticmethod
    def validate_threshold(threshold_type: str, value: float) -> None:
        errors = {}
        if threshold_type not in {"OccupancyWarning", "OccupancyCritical", "DensityCritical"}:
            errors["threshold_type"] = "Invalid threshold type"
        if value < 0.0:
            errors["value"] = "Threshold value cannot be negative"

        if errors:
            raise CrowdValidationError(errors)
