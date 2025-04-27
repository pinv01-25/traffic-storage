import pytest
import os
import json
import asyncio
from storage_manager import upload_and_register, download_and_verify, convert_to_unix_timestamp

# Ruta de los archivos de prueba
INPUT_FOLDER = os.path.join(os.path.dirname(__file__), "../input")
VALID_FOLDER = os.path.join(INPUT_FOLDER, "valid_data")
INVALID_FOLDER = os.path.join(INPUT_FOLDER, "invalid_data")

@pytest.mark.asyncio
async def test_upload_valid_data():
    """Subir un JSON válido debería funcionar sin errores"""
    valid_file = os.path.join(VALID_FOLDER, "valid_data.json")

    # Cargar el contenido del JSON
    with open(valid_file, "r") as f:
        payload = json.load(f)

    await upload_and_register(payload) 
    assert True

@pytest.mark.asyncio
async def test_upload_invalid_data():
    """Subir un JSON inválido debería lanzar ValidationError"""
    invalid_file = os.path.join(INVALID_FOLDER, "invalid_data.json")

    with pytest.raises(Exception):
        await upload_and_register(invalid_file)

@pytest.mark.asyncio
async def test_download_valid_data():
    """Descargar un JSON válido debería funcionar sin errores"""
    valid_file = os.path.join(VALID_FOLDER, "valid_data.json")
    
    with open(valid_file, "r") as f:
        payload = json.load(f)

    await upload_and_register(payload)

    traffic_light_id = payload["traffic_light_id"]
    timestamp = convert_to_unix_timestamp(payload["timestamp"])
    data_type = 0 if payload["type"] == "data" else 1

    # Ahora usamos los valores correctos
    data = await download_and_verify(traffic_light_id, timestamp, data_type)

    assert data is not None