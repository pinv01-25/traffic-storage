import { ethers } from "hardhat";
import { expect } from "chai";
import { TrafficStorage } from "../typechain-types";

describe("TrafficStorage", function () {
  let trafficStorage: TrafficStorage;

  beforeEach(async () => {
    const TrafficStorageFactory = await ethers.getContractFactory(
      "TrafficStorage"
    );
    trafficStorage = (await TrafficStorageFactory.deploy()) as TrafficStorage;
  });

  it("should store and retrieve a record correctly", async function () {
    const trafficLightId = "TL_21";
    const timestamp = Math.floor(Date.now() / 1000);
    const cid = "QmTestCid123";
    const dataType = 0; // DataType.Data (enum 0)

    // Store the record
    const tx = await trafficStorage.storeRecord(
      trafficLightId,
      timestamp,
      dataType,
      cid
    );
    await tx.wait();

    // Retrieve the record
    const storedCid = await trafficStorage.getRecord(
      trafficLightId,
      timestamp,
      dataType
    );
    expect(storedCid).to.equal(cid);
  });

  it("should revert when trying to retrieve a non-existent record", async function () {
    await expect(
      trafficStorage.getRecord("NonexistentTL", 0, 0)
    ).to.be.revertedWith("Record not found");
  });
});
