"use client";

import { useState } from "react";
import { useChainId } from "wagmi";
import { config } from "@/config";
import { MULTI_BATCH_CONTRACT_ABI } from "../lib/ABI";
import { Transaction } from "@/types/types";
import { ethers } from "ethers";
import { adminWallet } from "@/lib/USDCWallets";

export default function useExecuteMultiBatchContract() {
  const chainId = useChainId();
  const chain = config.chains.find((c) => c.id === chainId);

  if (!chain) {
    throw new Error("unsupported chain");
  }

  const [manualStatus, setManualStatus] = useState<string>("");
  const [receipt, setReceipt] = useState<ethers.TransactionReceipt | null>(
    null,
  );

  const contractAddress = chain?.contracts?.multiBatch?.address
    ? (chain.contracts.multiBatch.address as `0x${string}`)
    : undefined;

  /* // Prepare recipients and amounts arrays
  const recipientAddresses = recipients.map(
    (r) => r.address
  ) as `0x${string}`[];

  // Get actual wallet addresses from private keys
  const senderAddresses = sendersPrivateKeys.map(
    (sender) => new ethers.Wallet(sender.address).address
  ) as `0x${string}`[]; */

  //const amounts = senderAddresses.map(() => getRandomAmount()); //random value for each transaction

  const executeMultiBatch = async (batch: Transaction[]) => {
    try {
      setManualStatus("Preparing Multi Batch Transfer...");

      // Check if contract address is available
      if (!contractAddress) {
        setManualStatus("Contract address not found for this chain!");
        return;
      }

      // derive arrays from the batch argument
      const senders = batch.map((tx) => tx.sender) as `0x${string}`[];
      const recipientsArr = batch.map((tx) => tx.recipient) as `0x${string}`[];
      const amounts = batch.map((tx) => tx.amount);

      setManualStatus("Connecting admin wallet...");

      // Connect to the chain using admin wallet's private key
      const RPC_URL = chain.rpcUrls.default.http[0];
      const provider = new ethers.JsonRpcProvider(RPC_URL);
      const wallet = new ethers.Wallet(adminWallet.privateKey, provider);
      // Create contract instance
      const contract = new ethers.Contract(
        contractAddress,
        MULTI_BATCH_CONTRACT_ABI,
        wallet,
      );

      setManualStatus("Sending batch transaction...");

      // Call the smart contract with admin wallet
      const tx = await contract.executeBatch(senders, recipientsArr, amounts);

      setManualStatus("Waiting for confirmation...");

      // Wait for the transaction to be mined
      const txReceipt = await tx.wait();

      setManualStatus(`Transaction confirmed! Hash: ${tx.hash}`);
      setReceipt(txReceipt);

      return txReceipt;
    } catch (error) {
      console.error("Error:", error);
      setManualStatus(
        `Error: ${error instanceof Error ? error.message : "Unknown error"}`,
      );
      throw error;
    }
  };

  return {
    executeMultiBatch,
    status,
    receipt,
  };
}
