from enum import IntEnum, Enum

class DataType(IntEnum):
    """Data type enumeration for BlockDAG contract compatibility."""
    DATA = 0
    OPTIMIZATION = 1

class DataVersion(str, Enum):
    """Data version enumeration."""
    V1_0 = "1.0"
    V2_0 = "2.0"

class DataTypeString(str, Enum):
    """Data type string enumeration for API compatibility."""
    DATA = "data"
    OPTIMIZATION = "optimization" 