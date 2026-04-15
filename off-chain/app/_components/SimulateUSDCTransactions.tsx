"use client";

import React, { useMemo, useState } from "react";
import type { Transaction } from "@/types/types";
import { generateRandomTransaction } from "@/lib/generateRandomUSDCTransaction";
import { ethers } from "ethers";
import { ETH_BATCH_CONTRACT_ABI } from "@/lib/ABI";
import { adminWallet } from "@/lib/ethereum-wallets";

type TransactionWithGas = Transaction & { gasUsed: string };

const HARDHAT_RPC_URL = "http://127.0.0.1:8545";
const USDC_ADDRESS = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48";
const BATCH_CONTRACT_ADDRESS = process.env
  .NEXT_PUBLIC_ETHEREUM_BATCHER_ADDRESS as `0x${string}`;
const USDC_ABI = [
  {
    name: "transfer",
    type: "function",
    stateMutability: "nonpayable",
    inputs: [
      { name: "to", type: "address", internalType: "address" },
      { name: "amount", type: "uint256", internalType: "uint256" },
    ],
    outputs: [{ name: "", type: "bool", internalType: "bool" }],
  },
] as const;

async function executeBatch(
  batch: TransactionWithGas[],
  batcherWallet: ethers.Wallet,
  provider: ethers.JsonRpcProvider,
) {
  if (!BATCH_CONTRACT_ADDRESS) {
    console.error(
      "Missing NEXT_PUBLIC_ETHEREUM_BATCHER_ADDRESS. Set it in off-chain/.env.local and restart dev server.",
    );
    return;
  }

  if (batch.length === 0) {
    console.log(`\n⚠️ No transactions to batch. Skipping...`);
    return;
  }

  const contract = new ethers.Contract(
    BATCH_CONTRACT_ADDRESS,
    ETH_BATCH_CONTRACT_ABI,
    batcherWallet,
  );

  try {
    const signatures: string[] = [];
    const senders = [];
    const recipients = [];
    const amounts = [];

    const senderNoncesMap = new Map<string, bigint>();
    const batchSnapshot = [...batch];

    //every sender needs to sign the transaction to be included in the batch
    for (let i = 0; i < batchSnapshot.length; i++) {
      const tx = batchSnapshot[i];

      const senderWallet = new ethers.Wallet(
        tx.senderPrivateKey as string,
        provider,
      );

      let nonce: bigint;

      if (senderNoncesMap.has(tx.sender)) {
        nonce = senderNoncesMap.get(tx.sender)!;
        senderNoncesMap.set(tx.sender, nonce + BigInt(1));
      } else {
        nonce = await contract.nonces(tx.sender);
        senderNoncesMap.set(tx.sender, nonce + BigInt(1));
      }

      const messageHash = ethers.solidityPackedKeccak256(
        ["address", "address", "uint256", "uint256"],
        [tx.sender, tx.recipient, tx.amount, nonce],
      );

      const signature = await senderWallet.signMessage(
        ethers.getBytes(messageHash),
      );

      signatures.push(signature);
      senders.push(tx.sender);
      recipients.push(tx.recipient);
      amounts.push(tx.amount);
    }

    const batchedTx = await contract.executeBatch(
      senders,
      recipients,
      amounts,
      signatures,
    );

    console.log(`\nBatch Tx Sent: ${batchedTx.hash}`);

    const batchedTxReceipt = await batchedTx.wait();

    return (
      batchedTxReceipt &&
      (typeof batchedTxReceipt.gasUsed === "bigint"
        ? batchedTxReceipt.gasUsed.toString()
        : String(batchedTxReceipt.gasUsed))
    );
  } catch (error) {
    console.error(`❌ Batch execution failed:`, error);
  }
}

export default function SimulateUSDCTransactions() {
  const [isRunning, setIsRunning] = useState(false);
  const [transactions, setTransactions] = useState<TransactionWithGas[]>([]);
  const [countdown, setCountdown] = useState<number>(0);
  const [simulationComplete, setSimulationComplete] = useState(false);
  const [batchGasUsed, setBatchGasUsed] = useState<string | null>(null);
  const provider = useMemo(
    () => new ethers.JsonRpcProvider(HARDHAT_RPC_URL),
    [],
  );
  const batcherWallet = useMemo(
    () => new ethers.Wallet(adminWallet.privateKey, provider),
    [provider],
  );

  const processNewTransaction = async () => {
    try {
      const transaction = await generateRandomTransaction();

      const recipient = transaction.recipient;
      const txamount = transaction.amount;
      const individualWallet = new ethers.Wallet(
        transaction.senderPrivateKey as string,
        provider,
      );
      const individualUsdc = new ethers.Contract(
        USDC_ADDRESS,
        USDC_ABI,
        individualWallet,
      );

      const tx = await individualUsdc.transfer(recipient, txamount);
      const txReceipt = await tx.wait();

      const gasUsed =
        txReceipt?.gasUsed !== undefined
          ? typeof txReceipt.gasUsed === "bigint"
            ? txReceipt.gasUsed.toString()
            : String(txReceipt.gasUsed)
          : "0";

      console.log(`\n✅ Individual Tx: ${tx.hash}`);
      console.log(`⛽ Gas Used: ${gasUsed}`);

      return { ...transaction, gasUsed };
    } catch (txError) {
      console.error("Transaction failed:", txError);
      return null;
    }
  };

  const handleSimulation = async () => {
    setIsRunning(true);
    setTransactions([]);
    setSimulationComplete(false);
    setBatchGasUsed(null);
    setCountdown(120);
    const batch: TransactionWithGas[] = [];

    // start the countdown and simulation
    const simulationDuration = countdown * 1000;
    const endTime = Date.now() + simulationDuration;

    // Countdown timer
    const countdownInterval = setInterval(() => {
      const remaining = Math.ceil((endTime - Date.now()) / 1000);
      setCountdown(remaining > 0 ? remaining : 0);
    }, 1000);

    while (Date.now() < endTime) {
      const newTx = await processNewTransaction();

      if (newTx) {
        batch.push(newTx);
        setTransactions((prev) => [...prev, newTx]);
      }

      // wait random time
      await new Promise((r) => setTimeout(r, Math.random() * 3000));
    }

    clearInterval(countdownInterval);
    const gasUsed = await executeBatch(batch, batcherWallet, provider);
    setBatchGasUsed(gasUsed ?? null);

    setIsRunning(false);
    setSimulationComplete(true);
  };

  const totalIndividualGas = transactions.reduce(
    (sum, tx) => sum + BigInt(tx.gasUsed),
    BigInt(0),
  );

  return (
    <div className="max-w-6xl mx-auto p-8">
      <div className="bg-white shadow-lg rounded-lg p-6">
        <h1 className="text-3xl font-bold mb-6 text-gray-800">
          Transaction Batching Simulation
        </h1>

        {!isRunning && (
          <button
            onClick={handleSimulation}
            className="bg-blue-600 hover:bg-blue-700 text-white font-semibold px-6 py-3 mb-6 rounded-lg transition"
          >
            Start Simulation
          </button>
        )}

        {isRunning && (
          <div className="mb-6">
            <div className="flex items-center gap-4">
              <div className="text-2xl font-bold text-blue-600">
                {countdown > 0 ? `${countdown}s remaining` : "Simulation over"}
              </div>
              {countdown > 0 && (
                <div className="text-sm text-gray-500">Keep the tab open</div>
              )}
            </div>
          </div>
        )}

        {transactions.length > 0 && (
          <div className="mt-6">
            <h2 className="text-xl font-semibold mb-4 text-gray-700">
              Individual Transactions ({transactions.length})
            </h2>
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {transactions.map((tx, index) => (
                <div
                  key={index}
                  className="bg-gray-50 border border-gray-200 rounded p-3 text-sm"
                >
                  <div className="grid grid-cols-4 gap-4">
                    <div>
                      <span className="text-gray-500">From:</span>
                      <div className="font-mono text-xs  text-black">
                        {tx.sender.slice(0, 6)}...{tx.sender.slice(-4)}
                      </div>
                    </div>
                    <div>
                      <span className="text-gray-500">To:</span>
                      <div className="font-mono text-xsm text-black">
                        {tx.recipient.slice(0, 6)}...{tx.recipient.slice(-4)}
                      </div>
                    </div>
                    <div>
                      <span className="text-gray-500">Amount:</span>
                      <div className="font-semibold text-black">
                        {Number(tx.amount) / 1000000} USDC
                      </div>
                    </div>
                    <div>
                      <span className="text-gray-500">Gas:</span>
                      <div className="font-bold text-orange-600 bg-orange-50 px-2 py-1 rounded">
                        {tx.gasUsed}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {simulationComplete && (
          <div className="mt-8 bg-blue-50 border-2 border-blue-200 rounded-lg p-6">
            <h2 className="text-2xl font-bold mb-4 text-gray-800">
              Gas Comparison
            </h2>
            <div className="grid grid-cols-2 gap-6">
              <div className="bg-white rounded-lg p-4 shadow">
                <div className="text-gray-500 mb-2">Total Individual Gas</div>
                <div className="text-3xl font-bold text-red-600">
                  {totalIndividualGas.toString()}
                </div>
                <div className="text-sm text-gray-500 mt-1">
                  {transactions.length} transactions
                </div>
              </div>
              <div className="bg-white rounded-lg p-4 shadow">
                <div className="text-gray-500 mb-2">Batched Gas</div>
                <div className="text-3xl font-bold text-green-600">
                  {batchGasUsed ?? "N/A"}
                </div>
                <div className="text-sm text-gray-500 mt-1">
                  Single batch transaction
                </div>
              </div>
            </div>
            {batchGasUsed && (
              <div className="mt-4 text-center">
                <div className="text-lg font-semibold text-gray-700">
                  Gas Saved:{" "}
                  <span className="text-green-600">
                    {(totalIndividualGas - BigInt(batchGasUsed)).toString()}
                  </span>
                </div>
                <div className="text-sm text-gray-500">
                  {(
                    (Number(totalIndividualGas - BigInt(batchGasUsed)) /
                      Number(totalIndividualGas)) *
                    100
                  ).toFixed(2)}
                  % reduction
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
