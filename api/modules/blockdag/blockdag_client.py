from dotenv import load_dotenv
load_dotenv()

from web3 import Web3
import os
import asyncio

w3 = Web3(Web3.HTTPProvider('https://rpc.primordial.bdagscan.com'))

RPC_URL = os.getenv("RPC_URL", "https://rpc.primordial.bdagscan.com")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
account = w3.eth.account.from_key(PRIVATE_KEY)
SENDER_ADDRESS = account.address
CHAIN_ID = int(os.getenv("CHAIN_ID"))

w3 = Web3(Web3.HTTPProvider(RPC_URL))

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

async def store_metadata_in_blockdag(
    traffic_light_id: str,
    timestamp: int,
    data_type: int,
    cid: str
):
    MAX_RETRIES = 3
    base_gas_price = w3.to_wei("10", "gwei")

    for attempt in range(MAX_RETRIES):
        try:
            nonce = w3.eth.get_transaction_count(SENDER_ADDRESS, "pending")
            gas_price = base_gas_price + attempt * w3.to_wei("2", "gwei")

            tx = contract.functions.storeRecord(
                traffic_light_id,
                timestamp,
                data_type,
                cid
            ).build_transaction({
                "from": SENDER_ADDRESS,
                "nonce": nonce,
                "gas": 300000,
                "gasPrice": gas_price,
                "chainId": CHAIN_ID
            })

            signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

            print(f"Transaction sent: {tx_hash.hex()}")

            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            print(f"Transaction mined: {receipt.transactionHash.hex()}")
            return receipt

        except Exception as e:
            error_msg = str(e)
            print(f"[Attempt {attempt+1}] Error: {error_msg}")

            if ("replacement transaction underpriced" in error_msg or
                "nonce too low" in error_msg or
                "already known" in error_msg):
                print(f"[Attempt {attempt+1}] Retrying with higher gas price...")
                await asyncio.sleep(2)
                continue
            raise

    raise RuntimeError("Failed to send transaction after retries.")

async def fetch_metadata_from_blockdag(
    traffic_light_id: str, 
    timestamp: int, 
    data_type: int
) -> str:
    
    cid = contract.functions.getRecord(
        traffic_light_id,
        timestamp,
        data_type
    ).call()
    return cid