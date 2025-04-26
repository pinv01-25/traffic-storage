import { ethers } from "hardhat";

async function main() {
  const TrafficStorage = await ethers.getContractFactory("TrafficStorage");
  const trafficStorage = await TrafficStorage.deploy();

  await trafficStorage.waitForDeployment();

  const deploymentTransaction = await trafficStorage.deploymentTransaction();
  if (deploymentTransaction) {
    console.log(
      `TrafficStorage deployed at address: ${await trafficStorage.getAddress()}`
    );
  } else {
    console.error("Deployment transaction is null.");
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
