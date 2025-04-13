import { loadFixture } from "@nomicfoundation/hardhat-network-helpers";
import { expect } from "chai";
import { ethers } from "hardhat";

describe("TrafficStorage", function () {
  async function deployContract() {
    const TrafficStorage = await ethers.getContractFactory("TrafficStorage");
    const trafficStorage = await TrafficStorage.deploy();
    await trafficStorage.waitForDeployment();
    return { trafficStorage };
  }

  it("Should store and retrieve a CID correctly", async () => {
    const { trafficStorage } = await loadFixture(deployContract);
    const testCID = "QmXoypizjW3WknFiJnKLwHChL72vedxjQkDDPJmXMo6uco";
    await trafficStorage.storeCID(testCID);
    expect(await trafficStorage.getCID()).to.equal(testCID);
  });

  it("Should return empty string if no CID is stored", async () => {
    const { trafficStorage } = await loadFixture(deployContract); // Contrato fresco
    expect(await trafficStorage.getCID()).to.equal("");
  });
});