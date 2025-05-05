from dotenv import load_dotenv
load_dotenv()
from web3 import Web3
import os
import asyncio
import random
import time

# Configuración de Web3
RPC_URL = os.getenv("RPC_URL", "https://rpc.primordial.bdagscan.com")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
CHAIN_ID = int(os.getenv("CHAIN_ID", "1043"))  # Valor por defecto para Primordial TestNet

w3 = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={'timeout': 60}))  # Aumentar timeout de las solicitudes
account = w3.eth.account.from_key(PRIVATE_KEY)
SENDER_ADDRESS = account.address

print(f"[INFO] Connected to network: {w3.is_connected()}")
print(f"[INFO] Using address: {SENDER_ADDRESS}")
print(f"[INFO] Chain ID: {CHAIN_ID}")

# Dirección del contrato
contract_address = "0xC3d520EBE9A9F52FC5E1519f17F5a9A01d8ac68f"

contract_abi = [{
        "anonymous": False,
        "inputs": [
            {"indexed": False, "internalType": "string", "name": "trafficLightId", "type": "string"},
            {"indexed": False, "internalType": "uint256", "name": "timestamp", "type": "uint256"},
            {"indexed": False, "internalType": "enum TrafficStorage.DataType", "name": "dataType", "type": "uint8"},
            {"indexed": False, "internalType": "string", "name": "cid", "type": "string"}
        ],
        "name": "RecordStored",
        "type": "event"
    },
    {
        "inputs": [
            {"internalType": "string", "name": "trafficLightId", "type": "string"},
            {"internalType": "uint256", "name": "timestamp", "type": "uint256"},
            {"internalType": "enum TrafficStorage.DataType", "name": "dataType", "type": "uint8"}
        ],
        "name": "getRecord",
        "outputs": [{"internalType": "string", "name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "string", "name": "trafficLightId", "type": "string"},
            {"internalType": "uint256", "name": "timestamp", "type": "uint256"},
            {"internalType": "enum TrafficStorage.DataType", "name": "dataType", "type": "uint8"},
            {"internalType": "string", "name": "cid", "type": "string"}
        ],
        "name": "storeRecord",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

contract = w3.eth.contract(address=contract_address, abi=contract_abi)

# Gestión de nonce con bloqueo para evitar condiciones de carrera
NONCE_LOCK = asyncio.Lock()

async def get_fresh_nonce():
    """Obtiene un nonce actualizado directamente de la blockchain"""
    try:
        nonce = w3.eth.get_transaction_count(SENDER_ADDRESS, "pending")
        print(f"[DEBUG] Fresh nonce fetched: {nonce}")
        return nonce
    except Exception as e:
        print(f"[ERROR] Error fetching nonce: {e}")
        # Esperar un poco y reintentar
        await asyncio.sleep(2)
        return w3.eth.get_transaction_count(SENDER_ADDRESS, "pending")

async def calculate_optimal_gas_price(attempt=0):
    """Calcula un precio de gas óptimo basado en el precio actual del gas en la red y el número de intento"""
    try:
        base_gas_price = w3.eth.gas_price
        # Ajustamos los multiplicadores para ser más agresivos desde el inicio
        # La red blockDAG podría requerir precios de gas más altos
        multipliers = [1.5, 2.0, 3.0, 5.0, 8.0]
        multiplier = multipliers[min(attempt, len(multipliers)-1)]
        
        # Añadimos un pequeño factor aleatorio para evitar colisiones con otras transacciones
        randomness = 1.0 + (random.random() * 0.1)  # Entre 1.0 y 1.1
        
        gas_price = int(base_gas_price * multiplier * randomness)
        print(f"[DEBUG] Base gas price: {base_gas_price}")
        print(f"[DEBUG] Calculated gas price: {gas_price} (multiplier: {multiplier})")
        return gas_price
    except Exception as e:
        print(f"[ERROR] Error calculating gas price: {e}")
        # Valor por defecto en caso de error, más alto que antes
        return int(10_000_000_000 * (1.5 ** attempt))

async def store_metadata_in_blockdag(
    traffic_light_id: str,
    timestamp: int,
    data_type: int,
    cid: str
):
    MAX_RETRIES = 7  # Aumentamos el número máximo de reintentos

    last_error = None
    
    # Antes de intentar cualquier transacción, verificamos la conexión
    node_status = await check_blockdag_node_status()
    print(f"[INFO] BlockDAG node status: Connected={node_status['connected']}, Block={node_status.get('block_number')}")
    
    # Verificamos el balance para asegurarnos de tener fondos suficientes
    try:
        balance = w3.eth.get_balance(SENDER_ADDRESS)
        print(f"[INFO] Account balance: {w3.from_wei(balance, 'ether')} ETH")
        if balance < 10**16:  # 0.01 ETH
            print(f"[WARNING] Low balance: {w3.from_wei(balance, 'ether')} ETH")
    except Exception as e:
        print(f"[WARNING] Could not check balance: {e}")
    
    for attempt in range(MAX_RETRIES):
        try:
            print(f"[INFO] Attempt {attempt + 1} to store metadata")
            print(f"[INFO] Traffic Light ID: {traffic_light_id}, Timestamp: {timestamp}, CID: {cid}")
            
            # Obtener un nonce fresco con cada intento
            async with NONCE_LOCK:
                nonce = await get_fresh_nonce()
                print(f"[DEBUG] Using nonce: {nonce}")
            
            # Calcular un precio de gas adecuado
            gas_price = await calculate_optimal_gas_price(attempt)
            
            # Incluimos un tiempo de espera exponencial entre intentos
            if attempt > 0:
                backoff_time = min(2 ** attempt, 30)  # Máximo 30 segundos
                print(f"[DEBUG] Waiting {backoff_time} seconds before retry")
                await asyncio.sleep(backoff_time)
            
            # Construir la transacción - usamos solo gasPrice tradicional, no EIP-1559
            tx = contract.functions.storeRecord(
                traffic_light_id,
                timestamp,
                data_type,
                cid
            ).build_transaction({
                "from": SENDER_ADDRESS,
                "nonce": nonce,
                "gas": 400000,  # Aumentamos el límite de gas
                "gasPrice": gas_price,
                "chainId": CHAIN_ID
            })
            
            print(f"[DEBUG] Built transaction: {tx}")
            
            # Simular la transacción antes de enviarla
            try:
                w3.eth.call({
                    "to": tx["to"],
                    "data": tx["data"],
                    "from": SENDER_ADDRESS
                }, "pending")
                print("[DEBUG] Transaction simulation succeeded")
            except Exception as call_error:
                print(f"[ERROR] Transaction simulation failed: {call_error}")
                raise RuntimeError(f"The transaction would probably fail: {call_error}")
            
            # Firmar y enviar la transacción
            signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
            tx_hash_hex = signed_tx.hash.hex()
            print(f"[DEBUG] Signed transaction: {tx_hash_hex}")
            
            tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            print(f"[INFO] Transaction sent: {tx_hash.hex()}")
            
            # Esperar por el recibo con un timeout más largo
            receipt = await asyncio.to_thread(
                w3.eth.wait_for_transaction_receipt, 
                tx_hash, 
                timeout=300  # 5 minutos de timeout
            )
            
            if receipt.status == 1:
                print(f"[SUCCESS] Transaction mined successfully: {receipt.transactionHash.hex()}")
                print(f"[SUCCESS] Block number: {receipt.blockNumber}")
                print(f"[SUCCESS] Gas used: {receipt.gasUsed}")
                return receipt
            else:
                print(f"[ERROR] Transaction failed on-chain: {receipt}")
                raise RuntimeError("Transaction reverted or failed on-chain")
                
        except Exception as e:
            last_error = e
            error_msg = str(e)
            print(f"[ERROR] [Attempt {attempt+1}] Error: {error_msg}")
            
            # Analizar el error para decidir cómo manejarlo
            if any(err in error_msg for err in [
                "replacement transaction underpriced",
                "nonce too low",
                "already known",
                "Transaction with the same hash was already imported",
                "known transaction"
            ]):
                print("[DEBUG] Retrying due to known nonce-related error")
                # Esperar un momento antes del siguiente intento
                await asyncio.sleep(3)
                continue
                
            elif "is not in the chain after" in error_msg:
                print("[DEBUG] Transaction not mined in time, will retry with higher gas")
                # No necesitamos hacer nada especial, el próximo intento usará un gas más alto
                continue
                
            elif attempt < MAX_RETRIES - 1:
                # Otros errores, pero todavía tenemos intentos disponibles
                print(f"[DEBUG] Will retry. Error was: {error_msg}")
                continue
                
            # Si llegamos aquí, es el último intento y falló
            break
    
    # Si llegamos aquí, hemos agotado todos los intentos
    print("[ERROR] Failed to send transaction after all retries")
    raise RuntimeError(f"Failed to send transaction after {MAX_RETRIES} retries. Last error: {last_error}")

async def fetch_metadata_from_blockdag(
    traffic_light_id: str, 
    timestamp: int, 
    data_type: int
) -> str:
    """Recupera metadatos de la blockchain blockDAG"""
    try:
        cid = contract.functions.getRecord(
            traffic_light_id,
            timestamp,
            data_type
        ).call()
        return cid
    except Exception as e:
        print(f"[ERROR] Error fetching metadata from blockDAG: {e}")
        raise

# Función para comprobar el estado del nodo blockDAG
async def check_blockdag_node_status():
    """Verifica el estado del nodo blockDAG y devuelve información útil"""
    try:
        info = {
            "connected": w3.is_connected(),
            "block_number": w3.eth.block_number,
            "gas_price": w3.eth.gas_price,
            "chain_id": w3.eth.chain_id,
            "peer_count": w3.net.peer_count if hasattr(w3.net, 'peer_count') else "N/A"
        }
        return info
    except Exception as e:
        return {"error": str(e), "connected": False}

# Función de diagnóstico que puede llamarse para verificar la configuración
async def diagnose_connection():
    """Realiza un diagnóstico de la conexión a blockDAG"""
    status = await check_blockdag_node_status()
    print(f"[DIAGNOSTIC] BlockDAG Node Status: {status}")
    
    try:
        balance = w3.eth.get_balance(SENDER_ADDRESS)
        print(f"[DIAGNOSTIC] Account balance: {w3.from_wei(balance, 'ether')} ETH")
    except Exception as e:
        print(f"[DIAGNOSTIC] Error getting balance: {e}")
    
    return "Diagnosis complete"