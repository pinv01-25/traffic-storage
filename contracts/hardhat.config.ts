import { HardhatUserConfig } from "hardhat/config";
import "@nomicfoundation/hardhat-toolbox";
import "dotenv/config";

const config: HardhatUserConfig = {
  solidity: "0.8.19",
  networks: {
    blockdag: {
      url: "https://rpc.primordial.bdagscan.com",
      accounts: [process.env.PRIVATE_KEY!],
      chainId: 1043,
    },
  },
};

export default config;
