import re
from typing import Any, Dict
from config.settings import settings

def validate_traffic_light_id(traffic_light_id: str) -> bool:
    """
    Validate traffic light ID format.
    
    Args:
        traffic_light_id: Traffic light ID to validate
        
    Returns:
        True if valid
        
    Raises:
        ValueError: If validation fails
    """
    if not re.match(r'^\d+$', traffic_light_id):
        raise ValueError(f"Invalid traffic_light_id format: {traffic_light_id}. Expected only numbers.")
    return True

def validate_sensor_count(sensors: list) -> bool:
    """
    Validate sensor count in batch.
    
    Args:
        sensors: List of sensors to validate
        
    Returns:
        True if valid
        
    Raises:
        ValueError: If validation fails
    """
    count = len(sensors)
    if count < settings.MIN_SENSORS_PER_BATCH:
        raise ValueError(f"Too few sensors: {count}. Minimum required: {settings.MIN_SENSORS_PER_BATCH}")
    if count > settings.MAX_SENSORS_PER_BATCH:
        raise ValueError(f"Too many sensors: {count}. Maximum allowed: {settings.MAX_SENSORS_PER_BATCH}")
    return True

def validate_timestamp(timestamp: int) -> bool:
    """
    Validate Unix timestamp.
    
    Args:
        timestamp: Unix timestamp to validate
        
    Returns:
        True if valid
        
    Raises:
        ValueError: If validation fails
    """
    # Basic range validation (2000-2100)
    min_timestamp = 946684800  # 2000-01-01
    max_timestamp = 4102444800  # 2100-01-01
    
    if not isinstance(timestamp, int):
        raise ValueError(f"Timestamp must be an integer, got: {type(timestamp)}")
    
    if timestamp < min_timestamp or timestamp > max_timestamp:
        raise ValueError(f"Timestamp {timestamp} is outside valid range ({min_timestamp}-{max_timestamp})")
    
    return True

def validate_data_payload(data: Dict[str, Any]) -> bool:
    """
    Validate complete data payload.
    
    Args:
        data: Data payload to validate
        
    Returns:
        True if valid
        
    Raises:
        ValidationError: If validation fails
    """
    try:
        # Validate required fields
        required_fields = ["version", "type", "timestamp", "traffic_light_id"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate traffic light ID
        validate_traffic_light_id(data["traffic_light_id"])
        
        # Validate timestamp
        validate_timestamp(data["timestamp"])
        
        # Validate data type
        if data["type"] not in settings.DATA_TYPE_MAP:
            raise ValueError(f"Invalid data type: {data['type']}")
        
        # Validate sensors for data type
        if data["type"] == "data":
            if "sensors" not in data:
                raise ValueError("Missing 'sensors' field for data type")
            validate_sensor_count(data["sensors"])
        
        return True
        
    except ValueError as e:
        raise ValidationError(f"Data validation failed: {str(e)}") 