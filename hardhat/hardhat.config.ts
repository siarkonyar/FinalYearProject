import { HardhatUserConfig } from "hardhat/config";
import "@nomicfoundation/hardhat-toolbox";
import { HttpNetworkConfig } from "hardhat/types";
import "@nomicfoundation/hardhat-ethers";
import "@vechain/sdk-hardhat-plugin";
import * as dotenv from "dotenv";

dotenv.config(); // Add this line

const config: HardhatUserConfig = {
  solidity: {
    version: "0.8.28",
    settings: {
      optimizer: { enabled: true, runs: 200 },
      evmVersion: "paris", // or "shanghai" if needed
    },
  },
  networks: {
    //VeChain
    vechain_testnet: {
      url: process.env.VECHAIN_TESTNET_URL,
      accounts: {
        mnemonic: process.env.VECHAIN_TESTNET_MNEMONIC,
        path: "m/44'/818'/0'/0",
        count: 3,
        initialIndex: 0,
        passphrase: "vechainthor",
      },
      gas: "auto",
      gasPrice: "auto",
    },
    //hardhat node simulation
    hardhat: {
      forking: {
        url: process.env.ALCHEMY_MAINNET_URL ?? "",
      },
    },
  },
};

export default config;
