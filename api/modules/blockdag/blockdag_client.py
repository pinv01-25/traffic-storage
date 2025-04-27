from web3 import Web3

# Connect to BlockDAG testnet
w3 = Web3(Web3.HTTPProvider('http://localhost:8545'))

# Load contract
# contract_address = "0xC3d520EBE9A9F52FC5E1519f17F5a9A01d8ac68f"
contract_address = "0x5FbDB2315678afecb367f032d93F642f64180aa3"
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
    account = w3.eth.accounts[0]  # Use a funded account
    tx_hash = contract.functions.storeRecord(
        traffic_light_id,
        timestamp,
        data_type,  # Pass enum as uint8 (0 or 1)
        cid
    ).transact({"from": account})
    
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