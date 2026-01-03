import { createConfig, http } from "wagmi";
import { mainnet, sepolia } from "wagmi/chains";
import { defineChain } from "viem";
import { metaMask } from "wagmi/connectors";

// Define Hardhat local network with mainnet fork
const hardhatLocal = defineChain({
  id: 31337, // Hardhat's default chain ID
  name: "Hardhat Local (Mainnet Fork)",
  nativeCurrency: {
    decimals: 18,
    name: "Ether",
    symbol: "ETH",
  },
  rpcUrls: {
    default: {
      http: ["http://127.0.0.1:8545"],
    },
  },
  contracts: {
    myContract: {
      address: "0x5De0B97C21d65a9fd4a1512C3a191585e64a7868",
      blockCreated: 9945712,
    },
  },
});

export const config = createConfig({
  chains: [
    hardhatLocal,
    /* mainnet,
    sepolia, */
  ],
  //NOTE - this batch setting is comming from view
  batch: {
    multicall: {
      batchSize: 512,
      wait: 16,
    },
  },
  connectors: [
    metaMask({
      infuraAPIKey: process.env.NEXT_PUBLIC_INFURA_API_KEY!,
    }),
  ],
  transports: {
    [hardhatLocal.id]: http(),
    /* [mainnet.id]: http(),
    [sepolia.id]: http(), */
  },
});

declare module "wagmi" {
  interface Register {
    config: typeof config;
  }
}
