import { buildModule } from "@nomicfoundation/hardhat-ignition/modules";

export default buildModule("TrafficStorage", (m) => {
  const trafficStorage = m.contract("TrafficStorage");
  return { trafficStorage };
});