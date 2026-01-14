import { ethers } from "ethers";
import { sendersPrivateKeys } from "./keys";
import { config, tenderly } from "@/config";
import { useChainId } from "wagmi";

async function approveAll() {
  const TENDERLY_RPC = tenderly.rpcUrls.default.http[0];
  const USDC_ADDRESS = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"; // Mainnet USDC
  const BATCHER_CONTRACT_ADDRESS = tenderly.contracts.batcher.address;

  console.log("starting approvals...");

  //connect to tenderly
  const provider = new ethers.JsonRpcProvider(TENDERLY_RPC);

  const abi = [
    "function approve(address spender, uint256 amount) public returns (bool)",
  ];

  for (const sender of sendersPrivateKeys){
    
  }
}
