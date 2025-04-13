import { HardhatUserConfig } from "hardhat/config";
import "@nomicfoundation/hardhat-toolbox";
import "@nomicfoundation/hardhat-ethers";
import "@nomicfoundation/hardhat-ignition"; // Para despliegues con Ignition
import "dotenv/config"; // Para variables de entorno (opcional pero recomendado)

const config: HardhatUserConfig = {
  solidity: "0.8.28",
  networks: {
    // Red local de Hardhat (para pruebas)
    hardhat: {
      chainId: 31337, // Cadena por defecto de Hardhat
    },
    // Red Sepolia (para testnet)
    sepolia: {
      url: process.env.SEPOLIA_RPC_URL || "",
      accounts: process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : [],
      chainId: 11155111,
    },
  },
  // Configuración de Ignition (opcional)
  ignition: {
    blockPollingInterval: 1_000, // Para redes locales
  },
  // Verificación de contratos en Etherscan (opcional)
  etherscan: {
    apiKey: process.env.ETHERSCAN_API_KEY || "",
  },
};

export default config;