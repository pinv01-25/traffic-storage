from dotenv import load_dotenv
load_dotenv()

from web3 import Web3
import os

# Connect to BlockDAG testnet
w3 = Web3(Web3.HTTPProvider('https://rpc.primordial.bdagscan.com'))

# Cargar configuración desde variables de entorno
RPC_URL = os.getenv("RPC_URL", "https://rpc.primordial.bdagscan.com")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
CHAIN_ID = int(os.getenv("CHAIN_ID", "31337"))  # 31337 para Hardhat local, 1043 para BlockDAG

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
    data_type: int,  # 0 for Data, 1 for Optimization (enum)
    cid: str
):
    if PRIVATE_KEY is None:
        raise ValueError("PRIVATE_KEY environment variable is not set.")

    account = w3.eth.account.from_key(PRIVATE_KEY)
    nonce = w3.eth.get_transaction_count(account.address)

    tx = contract.functions.storeRecord(
        traffic_light_id,
        timestamp,
        data_type,
        cid
    ).build_transaction({
        "from": account.address,
        "nonce": nonce,
        "gas": 300000,
        "gasPrice": w3.to_wei("10", "gwei"),
        "chainId": CHAIN_ID
    })

    signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"Transaction mined: {receipt.transactionHash.hex()}")

async def fetch_metadata_from_blockdag(
    traffic_light_id: str, 
    timestamp: int, 
    data_type: int
) -> str:
    # Debugging print statement
    print(f"Calling getRecord with traffic_light_id={traffic_light_id}, timestamp={timestamp}, data_type_enum={data_type}")
    
    # Call the smart contract function
    cid = contract.functions.getRecord(
        traffic_light_id,
        timestamp,
        data_type
    ).call()
    return cid