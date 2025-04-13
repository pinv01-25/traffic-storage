import { ethers } from "hardhat";
import { TrafficStorage } from "../typechain-types"; // Critical type import

async function main() {
  // 1. Get the contract factory with type info
  const TrafficStorageFactory = await ethers.getContractFactory("TrafficStorage");
  
  // 2. Connect to existing contract
  const contractAddress = "0xC3d520EBE9A9F52FC5E1519f17F5a9A01d8ac68f"; 
  const trafficStorage = TrafficStorageFactory.attach(contractAddress) as TrafficStorage;

  // 3. Get CID
  const cid = await trafficStorage.getCID();
  console.log("CID stored:", cid);
}

main().catch(error => {
  console.error("Error:", error);
  process.exit(1);
});