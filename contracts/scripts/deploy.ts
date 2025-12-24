import { ethers } from "hardhat";

async function main() {
  console.log("Starting TrafficStorage contract deployment...\n");

  // Get the deployer account
  const [deployer] = await ethers.getSigners();
  console.log("Deploying contracts with account:", deployer.address);

  // Check balance
  const balance = await ethers.provider.getBalance(deployer.address);
  console.log("Account balance:", ethers.formatEther(balance), "BDAG\n");

  if (balance === 0n) {
    console.error("ERROR: Account has no balance. Please fund your account first.");
    process.exitCode = 1;
    return;
  }

  // Deploy contract
  console.log("Deploying TrafficStorage contract...");
  const TrafficStorage = await ethers.getContractFactory("TrafficStorage");
  const trafficStorage = await TrafficStorage.deploy();

  console.log("Waiting for deployment confirmation...");
  await trafficStorage.waitForDeployment();

  const contractAddress = await trafficStorage.getAddress();
  const deploymentTransaction = await trafficStorage.deploymentTransaction();

  console.log("\n" + "=".repeat(60));
  console.log("✅ DEPLOYMENT SUCCESSFUL!");
  console.log("=".repeat(60));
  console.log(`Contract Address: ${contractAddress}`);
  
  if (deploymentTransaction) {
    console.log(`Transaction Hash: ${deploymentTransaction.hash}`);
  }

  console.log("\n" + "=".repeat(60));
  console.log("📝 NEXT STEPS:");
  console.log("=".repeat(60));
  console.log("1. Copy the contract address above");
  console.log("2. Update your .env file in the traffic-storage root directory:");
  console.log(`   BLOCKDAG_CONTRACT_ADDRESS=${contractAddress}`);
  console.log("\n3. Restart your traffic-storage service");
  console.log("\n4. Verify deployment at: https://bdagscan.com/address/" + contractAddress);
  console.log("=".repeat(60) + "\n");
}

main().catch((error) => {
  console.error("\n❌ DEPLOYMENT FAILED:");
  console.error(error);
  process.exitCode = 1;
});
