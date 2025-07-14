import asyncio
import random
from typing import Dict, Any
from web3 import Web3
from config.settings import settings
from config.logging_config import get_logger
from utils.exceptions import BlockDAGError

logger = get_logger(__name__)

class BlockDAGService:
    """Service for interacting with BlockDAG blockchain."""
    
    def __init__(self):
        self.rpc_url = settings.BLOCKDAG_RPC_URL
        self.chain_id = settings.BLOCKDAG_CHAIN_ID
        self.private_key = settings.BLOCKDAG_PRIVATE_KEY
        self.contract_address = settings.BLOCKDAG_CONTRACT_ADDRESS
        
        # Initialize Web3
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url, request_kwargs={'timeout': 60}))
        
        if self.private_key:
            self.account = self.w3.eth.account.from_key(self.private_key)
            self.sender_address = self.account.address
        else:
            self.account = None
            self.sender_address = None
        
        # Contract ABI
        self.contract_abi = [{
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
        }]
        
        # Initialize contract
        if self.contract_address:
            self.contract = self.w3.eth.contract(
                address=self.contract_address, 
                abi=self.contract_abi
            )
        else:
            self.contract = None
        
        # Nonce lock for thread safety
        self.nonce_lock = asyncio.Lock()
        
        logger.info(f"BlockDAG service initialized. Connected: {self.w3.is_connected()}")
        if self.sender_address:
            logger.info(f"Using address: {self.sender_address}")
    
    async def store_metadata(
        self, 
        traffic_light_id: str, 
        timestamp: int, 
        data_type: int, 
        cid: str
    ) -> Dict[str, Any]:
        """
        Store metadata in BlockDAG blockchain.
        
        Args:
            traffic_light_id: Traffic light identifier
            timestamp: Unix timestamp
            data_type: Data type (0 for data, 1 for optimization)
            cid: IPFS Content Identifier
            
        Returns:
            Transaction receipt
            
        Raises:
            BlockDAGError: If storage fails
        """
        if not self.contract or not self.private_key:
            raise BlockDAGError("BlockDAG contract not configured or private key missing")
        
        MAX_RETRIES = 7
        last_error = None
        
        # Check connection and balance
        node_status = await self._check_node_status()
        logger.info(f"BlockDAG node status: Connected={node_status['connected']}, Block={node_status.get('block_number')}")
        
        await self._check_balance()
        
        for attempt in range(MAX_RETRIES):
            try:
                logger.info(f"Attempt {attempt + 1} to store metadata for traffic_light_id: {traffic_light_id}")
                
                # Get fresh nonce
                async with self.nonce_lock:
                    nonce = await self._get_fresh_nonce()
                    logger.debug(f"Using nonce: {nonce}")
                
                # Calculate optimal gas price
                gas_price = await self._calculate_optimal_gas_price(attempt)
                
                # Exponential backoff between attempts
                if attempt > 0:
                    backoff_time = min(2 ** attempt, 30)
                    logger.debug(f"Waiting {backoff_time} seconds before retry")
                    await asyncio.sleep(backoff_time)
                
                # Build transaction
                tx = self.contract.functions.storeRecord(
                    traffic_light_id,
                    timestamp,
                    data_type,
                    cid
                ).build_transaction({
                    "from": self.sender_address,
                    "nonce": nonce,
                    "gas": 400000,
                    "gasPrice": gas_price,
                    "chainId": self.chain_id
                })
                
                # Simulate transaction
                await self._simulate_transaction(tx)
                
                # Sign and send transaction
                signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
                tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
                logger.info(f"Transaction sent: {tx_hash.hex()}")
                
                # Wait for receipt
                receipt = await asyncio.to_thread(
                    self.w3.eth.wait_for_transaction_receipt, 
                    tx_hash, 
                    timeout=300
                )
                
                if receipt.status == 1:
                    logger.info(f"Transaction mined successfully: {receipt.transactionHash.hex()}")
                    logger.info(f"Block number: {receipt.blockNumber}, Gas used: {receipt.gasUsed}")
                    return receipt
                else:
                    raise RuntimeError("Transaction reverted or failed on-chain")
                    
            except Exception as e:
                last_error = e
                error_msg = str(e)
                logger.error(f"Attempt {attempt+1} failed: {error_msg}")
                
                # Handle specific error types
                if self._should_retry(error_msg):
                    logger.debug("Retrying due to known error type")
                    await asyncio.sleep(3)
                    continue
                elif attempt < MAX_RETRIES - 1:
                    logger.debug(f"Will retry. Error was: {error_msg}")
                    continue
                break
        
        # All retries exhausted
        logger.error(f"Failed to send transaction after {MAX_RETRIES} retries")
        raise BlockDAGError(f"Failed to send transaction after {MAX_RETRIES} retries. Last error: {last_error}")
    
    async def fetch_metadata(
        self, 
        traffic_light_id: str, 
        timestamp: int, 
        data_type: int
    ) -> str:
        """
        Fetch metadata from BlockDAG blockchain.
        
        Args:
            traffic_light_id: Traffic light identifier
            timestamp: Unix timestamp
            data_type: Data type (0 for data, 1 for optimization)
            
        Returns:
            IPFS Content Identifier
            
        Raises:
            BlockDAGError: If fetch fails
        """
        if not self.contract:
            raise BlockDAGError("BlockDAG contract not configured")
        
        try:
            logger.debug(f"Fetching metadata for traffic_light_id: {traffic_light_id}, timestamp: {timestamp}")
            
            cid = self.contract.functions.getRecord(
                traffic_light_id,
                timestamp,
                data_type
            ).call()
            
            logger.info(f"Successfully fetched CID: {cid}")
            return cid
            
        except Exception as e:
            logger.error(f"Error fetching metadata from BlockDAG: {str(e)}")
            raise BlockDAGError(f"Failed to fetch metadata: {str(e)}")
    
    def check_connectivity(self) -> bool:
        """
        Check BlockDAG connectivity.
        
        Returns:
            True if BlockDAG is accessible
        """
        try:
            return self.w3.is_connected()
        except Exception as e:
            logger.warning(f"BlockDAG connectivity check failed: {str(e)}")
            return False
    
    async def _get_fresh_nonce(self) -> int:
        """Get fresh nonce from blockchain."""
        try:
            nonce = self.w3.eth.get_transaction_count(self.sender_address, "pending")
            return nonce
        except Exception as e:
            await asyncio.sleep(2)
            return self.w3.eth.get_transaction_count(self.sender_address, "pending")
    
    async def _calculate_optimal_gas_price(self, attempt: int = 0) -> int:
        """Calculate optimal gas price based on current network conditions."""
        try:
            base_gas_price = self.w3.eth.gas_price
            multipliers = [1.5, 2.0, 3.0, 5.0, 8.0]
            multiplier = multipliers[min(attempt, len(multipliers)-1)]
            randomness = 1.0 + (random.random() * 0.1)
            gas_price = int(base_gas_price * multiplier * randomness)
            return gas_price
        except Exception as e:
            logger.error(f"Error calculating gas price: {e}")
            return int(10_000_000_000 * (1.5 ** attempt))
    
    async def _simulate_transaction(self, tx: Dict[str, Any]) -> None:
        """Simulate transaction before sending."""
        try:
            self.w3.eth.call({
                "to": tx["to"],
                "data": tx["data"],
                "from": self.sender_address
            }, "pending")
        except Exception as e:
            logger.error(f"Transaction simulation failed: {e}")
            raise RuntimeError(f"Transaction would probably fail: {e}")
    
    async def _check_node_status(self) -> Dict[str, Any]:
        """Check BlockDAG node status."""
        try:
            info = {
                "connected": self.w3.is_connected(),
                "block_number": self.w3.eth.block_number,
                "gas_price": self.w3.eth.gas_price,
                "chain_id": self.w3.eth.chain_id
            }
            return info
        except Exception as e:
            return {"error": str(e), "connected": False}
    
    async def _check_balance(self) -> None:
        """Check account balance."""
        try:
            balance = self.w3.eth.get_balance(self.sender_address)
            logger.info(f"Account balance: {self.w3.from_wei(balance, 'ether')} ETH")
            if balance < 10**16:  # 0.01 ETH
                logger.warning(f"Low balance: {self.w3.from_wei(balance, 'ether')} ETH")
        except Exception as e:
            logger.warning(f"Could not check balance: {e}")
    
    def _should_retry(self, error_msg: str) -> bool:
        """Determine if error should trigger a retry."""
        retry_errors = [
            "replacement transaction underpriced",
            "nonce too low",
            "already known",
            "Transaction with the same hash was already imported",
            "known transaction"
        ]
        return any(err in error_msg for err in retry_errors) 