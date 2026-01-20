import { generateRandomTransaction } from "../lib/generateRandomTransaction";
import { adminWallet } from "../lib/keys";
import { ethers } from "ethers";
import type { Transaction } from "../types/types";
import { MULTI_BATCH_CONTRACT_ABI } from "../lib/ABI";
import * as dotenv from "dotenv";

dotenv.config();

const HARDHAT_RPC_URL = "http://127.0.0.1:8545";
const USDC_ADDRESS = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48";
const MULTI_BATCH_ADDRESS = process.env
  .NEXT_PUBLIC_BATCHER_ADDRESS as `0x${string}`;
const SIMULATION_DURATION = 0.2 * 60 * 1000; // 12 seconds
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

//batching variables
const BATCH_SIZE = 5
const BATCH_INTERVAL_IN_MIN = 15

async function USDCSimulation() {
  console.log("Starting Background Worker...");

  // RE-CREATE YOUR HOOK LOGIC HERE MANUALLY
  // You cannot use 'useProvider', you must create one:
  const provider = new ethers.JsonRpcProvider(HARDHAT_RPC_URL);
  const batcherWallet = new ethers.Wallet(adminWallet.privateKey, provider);

  const endTime = Date.now() + SIMULATION_DURATION;
  const batch: Transaction[] = [];

  // Send countdown updates
  const countdownInterval = setInterval(() => {
    const remaining = Math.ceil((endTime - Date.now()) / 1000);
    if (remaining > 0) {
      process.stdout.write(`\r⏳ Remaining time: ${remaining}s `);
    } else {
      process.stdout.write(`\r⌛ Time Window Closed.       \n`);
      clearInterval(countdownInterval);
    }
  }, 1000);

  try {
    while (Date.now() < endTime) {
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

      try {
        const tx = await individualUsdc.transfer(recipient, txamount);
        const txReceipt = await tx.wait();

        const gasUsed =
          txReceipt &&
          (typeof txReceipt.gasUsed === "bigint"
            ? txReceipt.gasUsed.toString()
            : String(txReceipt.gasUsed));

        console.log(`\n✅ Individual Tx: ${tx.hash}`);
        console.log(`   Gas Used: ${gasUsed}`);

        batch.push(transaction);
      } catch (txError) {
        console.error("Transaction failed:", txError);
        continue;
      }

      //random delay
      await new Promise((r) => setTimeout(r, Math.random() * 3000));
    }

    console.log(`\n📦 Batching ${batch.length} transactions...`);

    const senders = batch.map((tx) => tx.sender) as `0x${string}`[];
    const recipientsArr = batch.map((tx) => tx.recipient) as `0x${string}`[];
    const amounts = batch.map((tx) => tx.amount);

    const contract = new ethers.Contract(
      MULTI_BATCH_ADDRESS,
      MULTI_BATCH_CONTRACT_ABI,
      batcherWallet,
    );

    const batchedTx = await contract.executeBatch(
      senders,
      recipientsArr,
      amounts,
    );

    console.log(`🚀 Batch Tx Sent: ${batchedTx.hash}`);

    const batchedTxReceipt = await batchedTx.wait();

    const batchGasUsed =
      batchedTxReceipt &&
      (typeof batchedTxReceipt.gasUsed === "bigint"
        ? batchedTxReceipt.gasUsed.toString()
        : String(batchedTxReceipt.gasUsed));

    console.log(`🎉 Batch Confirmed! Total Gas: ${batchGasUsed}`);
    console.log(`--- Simulation Complete ---`);
  } catch (error) {
    console.error("\n❌ FATAL ERROR:", error);
  } finally {
    clearInterval(countdownInterval);
  }
}

USDCSimulation()
  .then(() => process.exit(0))
  .catch((e) => {
    console.error(e);
    process.exit(1);
  });
