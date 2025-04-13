import { ethers } from "hardhat";
import { TrafficStorage__factory } from "../typechain-types";

async function main() {
  const contractAddress = "0xC3d520EBE9A9F52FC5E1519f17F5a9A01d8ac68f";
  const cid = "QmYWHLrV6hyxDRWhvg3bMFZXyNqFxqxAd3UdSyf8MaNu9A";

  // Use generated factory
  const signer = (await ethers.getSigners())[0];
  const trafficStorage = TrafficStorage__factory.connect(contractAddress, signer);

  const tx = await trafficStorage.storeCID(cid);
  console.log("Tx sent:", tx.hash);

  await tx.wait();
  console.log("✅ CID stored!");
}

main().catch((error) => {
  console.error("Error:", error);
  process.exit(1);
});
