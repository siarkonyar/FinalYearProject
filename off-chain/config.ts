import { createConfig, http } from "wagmi";
import { mainnet, sepolia } from "wagmi/chains";
import { defineChain } from "viem";
import { metaMask } from "wagmi/connectors";

const buildBearSandbox = defineChain({
  id: 31337, // REPLACE with your actual BuildBear Chain ID
  name: "BuildBear Sandbox",
  network: "buildbear",
  nativeCurrency: {
    decimals: 18,
    name: "BuildBear Ether",
    symbol: "ETH",
  },
  rpcUrls: {
    default: {
      http: [process.env.NEXT_PUBLIC_RPC_URL ?? ""], // REPLACE with your RPC URL
    },
    public: {
      http: [process.env.NEXT_PUBLIC_RPC_URL ?? ""],
    },
  },
  blockExplorers: {
    default: {
      name: "BuildBear Explorer",
      url: process.env.NEXT_PUBLIC_BUILDBEAR_BLOCK_EXPLORER_URL ?? "",
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
    /* mainnet,
    sepolia, */
    buildBearSandbox,
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
    [buildBearSandbox.id]: http(),
    /* [mainnet.id]: http(),
    [sepolia.id]: http(), */
  },
});

declare module "wagmi" {
  interface Register {
    config: typeof config;
  }
}
