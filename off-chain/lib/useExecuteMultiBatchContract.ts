"use client";

import { useMemo, useState } from "react";
import {
  useAccount,
  useWriteContract,
  useWaitForTransactionReceipt,
  useChainId,
  useBalance,
} from "wagmi";
import { formatEther, parseEther, parseUnits } from "viem";
import { config, tenderly } from "@/config";
import { recipients, sendersPrivateKeys } from "./keys";
import { MULTI_BATCH_CONTRACT_ABI } from "./ABI";

export default function useExecuteMultiBatchContract() {
  const chainId = useChainId();
  const chain = config.chains.find((c) => c.id === chainId);

  const [manualStatus, setManualStatus] = useState<string>("");

  const contractAddress =
    chain?.id === tenderly.id
      ? (tenderly.contracts.batcher.address as `0x${string}`)
      : undefined;

  const {
    data: hash,
    writeContractAsync,
    error: writeError,
    isPending,
  } = useWriteContract();

  const { isLoading: isConfirming, isSuccess: isConfirmed } =
    useWaitForTransactionReceipt({
      hash,
    });

  const status = useMemo(() => {
    if (writeError) {
      return `Error: ${writeError.message}`;
    }
    if (isConfirming) {
      return "Transaction pending... waiting for confirmation";
    }
    if (isConfirmed && hash) {
      return `Transaction confirmed! Hash: ${hash}`;
    }
    // Fall back to manual status for pre-transaction messages
    return manualStatus;
  }, [isConfirming, isConfirmed, hash, writeError, manualStatus]);

  const executeMultiBatch = async () => {
    try {
      setManualStatus("Preparing Multi Batch Transfer...");

      // Check if contract address is available
      if (!contractAddress) {
        setManualStatus("Contract address not found for this chain!");
        return;
      }

      // Prepare recipients and amounts arrays
      const recipientAddresses = recipients.map(
        (r) => r.address
      ) as `0x${string}`[];

      const senderAddresses = sendersPrivateKeys.map(
        (r) => r.address
      ) as `0x${string}`[];

      const amounts = senderAddresses.map(() => parseUnits("10", 6)); // 10 USDC for each



      setManualStatus("Waiting for transaction approval...");

      // Call the smart contract
      writeContractAsync({
        address: contractAddress,
        abi: MULTI_BATCH_CONTRACT_ABI,
        functionName: "executeBatch",
        args: [senderAddresses, recipientAddresses, amounts],
      });
    } catch (error) {
      console.error("Error:", error);
      setManualStatus(
        `Error: ${error instanceof Error ? error.message : "Unknown error"}`
      );
    }
  };
}
