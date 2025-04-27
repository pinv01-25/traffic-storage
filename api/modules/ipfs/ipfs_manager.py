import subprocess
import json
import asyncio

IPFS_API_URL = "http://127.0.0.1:5001/api/v0/version"

# --- Funciones internas ---

def run_ipfs_command(args):
    try:
        result = subprocess.run([
            "/usr/local/bin/ipfs", *args
        ], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"IPFS command failed: {e.stderr}")

# --- Funciones principales ---

async def upload_json_to_ipfs(data: dict) -> str:
    json_data = json.dumps(data)
    proc = subprocess.Popen(
        ["/usr/local/bin/ipfs", "add", "-q"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    stdout, stderr = proc.communicate(input=json_data)
    if proc.returncode != 0:
        raise RuntimeError(f"IPFS add failed: {stderr}")
    cid = stdout.strip()
    return cid

async def download_json_from_ipfs(cid: str) -> dict:
    proc = subprocess.Popen(
        ["/usr/local/bin/ipfs", "cat", cid],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    stdout, stderr = proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"IPFS cat failed: {stderr}")
    data = json.loads(stdout)
    return data

# --- Limpieza (opcional) ---
async def shutdown_ipfs():
    # No necesitamos shutdown manual ahora, porque ipfs daemon es separado
    pass
