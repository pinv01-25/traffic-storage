import asyncio
import random
from typing import Any, Dict

from config.logging_config import get_logger
from config.settings import settings
from modules.utils import BlockDAGError
from web3 import Web3

logger = get_logger(__name__, service_name="traffic_storage")


class BlockDAGService:
    """Service for interacting with BlockDAG blockchain."""

    def __init__(self):
        self.rpc_url = settings.BLOCKDAG_RPC_URL
        self.chain_id = settings.BLOCKDAG_CHAIN_ID
        self.private_key = settings.BLOCKDAG_PRIVATE_KEY
        self.contract_address = settings.BLOCKDAG_CONTRACT_ADDRESS

        # Validate RPC URL is not empty
        if not self.rpc_url or self.rpc_url.strip() == "":
            logger.warning("BLOCKDAG_RPC_URL is empty, using default")
            self.rpc_url = "https://relay.awakening.bdagscan.com/"

        # Initialize Web3 with longer timeout for health checks
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url, request_kwargs={"timeout": 30}))

        if self.private_key:
            self.account = self.w3.eth.account.from_key(self.private_key)
            self.sender_address = self.account.address
        else:
            self.account = None
            self.sender_address = None

        # Contract ABI
        self.contract_abi = [
            {
                "anonymous": False,
                "inputs": [
                    {
                        "indexed": False,
                        "internalType": "string",
                        "name": "trafficLightId",
                        "type": "string",
                    },
                    {
                        "indexed": False,
                        "internalType": "uint256",
                        "name": "timestamp",
                        "type": "uint256",
                    },
                    {
                        "indexed": False,
                        "internalType": "enum TrafficStorage.DataType",
                        "name": "dataType",
                        "type": "uint8",
                    },
                    {"indexed": False, "internalType": "string", "name": "cid", "type": "string"},
                ],
                "name": "RecordStored",
                "type": "event",
            },
            {
                "inputs": [
                    {"internalType": "string", "name": "trafficLightId", "type": "string"},
                    {"internalType": "uint256", "name": "timestamp", "type": "uint256"},
                    {
                        "internalType": "enum TrafficStorage.DataType",
                        "name": "dataType",
                        "type": "uint8",
                    },
                ],
                "name": "getRecord",
                "outputs": [{"internalType": "string", "name": "", "type": "string"}],
                "stateMutability": "view",
                "type": "function",
            },
            {
                "inputs": [
                    {"internalType": "string", "name": "trafficLightId", "type": "string"},
                    {"internalType": "uint256", "name": "timestamp", "type": "uint256"},
                    {
                        "internalType": "enum TrafficStorage.DataType",
                        "name": "dataType",
                        "type": "uint8",
                    },
                    {"internalType": "string", "name": "cid", "type": "string"},
                ],
                "name": "storeRecord",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function",
            },
        ]

        # Initialize contract
        if self.contract_address:
            # Validate and normalize contract address format (checksum)
            if not self.w3.is_address(self.contract_address):
                logger.error(f"Invalid contract address format: {self.contract_address}")
                raise BlockDAGError(f"Invalid contract address format: {self.contract_address}")
            
            # Convert to checksum address
            try:
                self.contract_address = self.w3.to_checksum_address(self.contract_address)
            except Exception as e:
                logger.error(f"Error converting contract address to checksum: {str(e)}")
                raise BlockDAGError(f"Invalid contract address: {str(e)}")
            
            # Check if contract code exists at address (only if connected)
            try:
                if self.w3.is_connected():
                    contract_code = self.w3.eth.get_code(self.contract_address)
                    if not contract_code or contract_code == "0x":
                        logger.warning(
                            f"No contract code found at address {self.contract_address}. "
                            "Contract may not be deployed or address is incorrect. "
                            "This will cause errors when trying to interact with the contract."
                        )
                    else:
                        logger.info(f"Contract code verified at address: {self.contract_address}")
                else:
                    logger.warning(
                        "Cannot verify contract deployment: not connected to network. "
                        "Contract verification will be skipped."
                    )
            except Exception as e:
                logger.warning(
                    f"Could not verify contract code (this may be normal if RPC is unavailable): {str(e)}"
                )
                # Don't raise here, allow initialization to continue
                # The error will be caught when actually trying to use the contract
            
            self.contract = self.w3.eth.contract(
                address=self.contract_address, abi=self.contract_abi
            )
        else:
            self.contract = None
            logger.warning("No contract address configured. BlockDAG operations will be limited.")

        # Nonce lock for thread safety
        self.nonce_lock = asyncio.Lock()

        logger.info(f"BlockDAG service initialized. Connected: {self.w3.is_connected()}")
        if self.sender_address:
            logger.info(f"Using address: {self.sender_address}")
        if self.contract_address:
            logger.info(f"Contract address: {self.contract_address}")

    async def store_metadata(
        self, traffic_light_id: str, timestamp: int, data_type: int, cid: str
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
        logger.info(
            f"BlockDAG node status: Connected={node_status['connected']}, Block={node_status.get('block_number')}"
        )

        await self._check_balance()

        for attempt in range(MAX_RETRIES):
            try:
                logger.info(
                    f"Attempt {attempt + 1} to store metadata for traffic_light_id: {traffic_light_id}"
                )

                # Get fresh nonce
                async with self.nonce_lock:
                    nonce = await self._get_fresh_nonce()
                    logger.debug(f"Using nonce: {nonce}")

                # Calculate optimal gas price
                gas_price = await self._calculate_optimal_gas_price(attempt)

                # Exponential backoff between attempts
                if attempt > 0:
                    backoff_time = min(2**attempt, 30)
                    logger.debug(f"Waiting {backoff_time} seconds before retry")
                    await asyncio.sleep(backoff_time)

                # Build transaction
                tx = self.contract.functions.storeRecord(
                    traffic_light_id, timestamp, data_type, cid
                ).build_transaction(
                    {
                        "from": self.sender_address,
                        "nonce": nonce,
                        "gas": 400000,
                        "gasPrice": gas_price,
                        "chainId": self.chain_id,
                    }
                )

                # Simulate transaction
                await self._simulate_transaction(tx)

                # Sign and send transaction
                signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
                tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
                logger.info(f"Transaction sent: {tx_hash.hex()}")

                # Wait for receipt
                receipt = await asyncio.to_thread(
                    self.w3.eth.wait_for_transaction_receipt, tx_hash, timeout=300
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
                logger.error(f"Attempt {attempt + 1} failed: {error_msg}")

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
        raise BlockDAGError(
            f"Failed to send transaction after {MAX_RETRIES} retries. Last error: {last_error}"
        )

    async def fetch_metadata(self, traffic_light_id: str, timestamp: int, data_type: int) -> str:
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

        # Verify connection before attempting call
        if not self.w3.is_connected():
            raise BlockDAGError(
                "Not connected to BlockDAG network. Please check RPC URL and network connectivity."
            )

        try:
            logger.debug(
                f"Fetching metadata for traffic_light_id: {traffic_light_id}, "
                f"timestamp: {timestamp}, data_type: {data_type}"
            )

            # Verify contract is still deployed
            contract_code = self.w3.eth.get_code(self.contract_address)
            if not contract_code or contract_code == "0x":
                raise BlockDAGError(
                    f"Contract not found at address {self.contract_address}. "
                    "Contract may have been removed or address is incorrect."
                )

            # Make the contract call
            cid = self.contract.functions.getRecord(traffic_light_id, timestamp, data_type).call()

            # Check if result is empty (contract might return empty string for non-existent records)
            if not cid or cid.strip() == "":
                logger.warning(
                    f"No record found for traffic_light_id: {traffic_light_id}, "
                    f"timestamp: {timestamp}, data_type: {data_type}"
                )
                raise BlockDAGError(
                    f"Record not found for traffic_light_id: {traffic_light_id}, "
                    f"timestamp: {timestamp}, data_type: {data_type}"
                )

            logger.info(f"Successfully fetched CID: {cid}")
            return cid

        except BlockDAGError:
            # Re-raise BlockDAGError as-is
            raise
        except ValueError as e:
            error_msg = str(e)
            # Check for common contract call errors
            if "execution reverted" in error_msg.lower():
                if "record not found" in error_msg.lower():
                    logger.warning(
                        f"Record not found in contract for traffic_light_id: {traffic_light_id}, "
                        f"timestamp: {timestamp}, data_type: {data_type}"
                    )
                    raise BlockDAGError(
                        f"Record not found for traffic_light_id: {traffic_light_id}, "
                        f"timestamp: {timestamp}, data_type: {data_type}"
                    )
                else:
                    logger.error(f"Contract execution reverted: {error_msg}")
                    raise BlockDAGError(f"Contract execution failed: {error_msg}")
            else:
                logger.error(f"Value error during contract call: {error_msg}")
                raise BlockDAGError(f"Invalid parameters or contract state: {error_msg}")
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error fetching metadata from BlockDAG: {error_msg}")
            
            # Provide more specific error messages
            if "could not transact" in error_msg.lower() or "call contract function" in error_msg.lower():
                raise BlockDAGError(
                    f"Failed to call contract function. Possible causes:\n"
                    f"1. Contract not deployed at address {self.contract_address}\n"
                    f"2. Chain not synced or RPC endpoint unavailable\n"
                    f"3. Contract ABI mismatch\n"
                    f"4. Network connectivity issues\n"
                    f"Original error: {error_msg}"
                )
            elif "connection" in error_msg.lower() or "timeout" in error_msg.lower():
                raise BlockDAGError(
                    f"Network connection error: {error_msg}. "
                    "Please check RPC URL and network connectivity."
                )
            else:
                raise BlockDAGError(f"Failed to fetch metadata: {error_msg}")

    def check_connectivity(self) -> bool:
        """
        Check BlockDAG connectivity by attempting to query the node and verify contract.

        Returns:
            True if BlockDAG is accessible and contract is deployed
        """
        try:
            # Check basic connection
            if not self.w3.is_connected():
                logger.warning("BlockDAG RPC is not connected")
                return False

            # Try to get the latest block number as a connectivity test
            # This actually makes a request to the RPC endpoint
            # Use a shorter timeout for health checks
            try:
                block_number = self.w3.eth.block_number
                chain_id = self.w3.eth.chain_id
            except Exception as e:
                logger.warning(f"Failed to get block number/chain ID: {str(e)}")
                return False

            # Verify chain ID matches expected value
            if chain_id != self.chain_id:
                logger.warning(f"Chain ID mismatch: expected {self.chain_id}, got {chain_id}")
                return False

            # Verify contract is deployed if address is configured
            if self.contract_address:
                try:
                    contract_code = self.w3.eth.get_code(self.contract_address)
                    if not contract_code or contract_code == "0x":
                        logger.warning(
                            f"Contract not deployed at address {self.contract_address}. "
                            "Connectivity check will return False."
                        )
                        return False
                except Exception as e:
                    logger.warning(f"Could not verify contract deployment: {str(e)}")
                    # Don't fail connectivity check if contract verification fails
                    # The connection itself is working, just contract verification had issues
                    pass

            logger.info(
                f"BlockDAG connectivity verified: block_number={block_number}, chain_id={chain_id}"
            )
            if self.contract_address:
                logger.info(f"Contract verified at: {self.contract_address}")
            return True
        except Exception as e:
            error_msg = str(e)
            # Provide more specific error messages
            if "Failed to resolve" in error_msg or "getaddrinfo failed" in error_msg:
                logger.warning(
                    f"BlockDAG DNS resolution failed for {self.rpc_url}. "
                    f"Check your network connection or verify the RPC URL is correct."
                )
            elif "Connection" in error_msg or "timeout" in error_msg.lower():
                logger.warning(
                    f"BlockDAG connection timeout to {self.rpc_url}. "
                    f"The RPC endpoint may be unavailable."
                )
            else:
                logger.warning(f"BlockDAG connectivity check failed: {error_msg}")
            return False

    async def _get_fresh_nonce(self) -> int:
        """Get fresh nonce from blockchain."""
        try:
            nonce = self.w3.eth.get_transaction_count(self.sender_address, "pending")
            return nonce
        except Exception:
            await asyncio.sleep(2)
            return self.w3.eth.get_transaction_count(self.sender_address, "pending")

    async def _calculate_optimal_gas_price(self, attempt: int = 0) -> int:
        """Calculate optimal gas price based on current network conditions."""
        try:
            base_gas_price = self.w3.eth.gas_price
            multipliers = [1.5, 2.0, 3.0, 5.0, 8.0]
            multiplier = multipliers[min(attempt, len(multipliers) - 1)]
            randomness = 1.0 + (random.random() * 0.1)
            gas_price = int(base_gas_price * multiplier * randomness)
            return gas_price
        except Exception as e:
            logger.error(f"Error calculating gas price: {e}")
            return int(10_000_000_000 * (1.5**attempt))

    async def _simulate_transaction(self, tx: Dict[str, Any]) -> None:
        """Simulate transaction before sending."""
        try:
            self.w3.eth.call(
                {"to": tx["to"], "data": tx["data"], "from": self.sender_address}, "pending"
            )
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
                "chain_id": self.w3.eth.chain_id,
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
            "known transaction",
        ]
        return any(err in error_msg for err in retry_errors)
