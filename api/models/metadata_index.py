# api/models/metadata_index.py

from sqlalchemy import Table, Column, String, TIMESTAMP
from api.database import metadata

metadata_index = Table(
    "metadata_index",
    metadata,
    Column("type", String, primary_key=True),  # "data" or "optimization"
    Column("timestamp", TIMESTAMP(timezone=True), primary_key=True),
    Column("traffic_light_id", String, primary_key=True),
)
