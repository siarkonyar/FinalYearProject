import {
  ProviderInternalBaseWallet,
  signerUtils,
  ThorClient,
  VeChainPrivateKeySigner,
  VeChainProvider,
} from "@vechain/sdk-network";
import {
  Clause,
  Address,
  VET,
  VTHO,
  TransactionClause,
  HexUInt,
  Transaction,
  TransactionBody,
  networkInfo,
  Account,
  Secp256k1,
  Hex,
  Units,
} from "@vechain/sdk-core";
import * as dotenv from "dotenv";
import { recipients, godWallet } from "../lib/vechain-wallets";
import { Mnemonic } from "@vechain/sdk-core";

dotenv.config();

// CONFIGURATION
const THOR_URL = "http://127.0.0.1:8669";
const USDC_ADDRESS = process.env.NEXT_PUBLIC_VECHAIN_USDC_ADDRESS as string;

const USDC_ABI = [
  {
    type: "constructor",
    inputs: [
      { name: "name_", type: "string", internalType: "string" },
      { name: "symbol_", type: "string", internalType: "string" },
      { name: "decimal_", type: "uint8", internalType: "uint8" },
    ],
    stateMutability: "nonpayable",
  },
  {
    name: "Approval",
    type: "event",
    inputs: [
      {
        name: "owner",
        type: "address",
        indexed: true,
        internalType: "address",
      },
      {
        name: "spender",
        type: "address",
        indexed: true,
        internalType: "address",
      },
      {
        name: "value",
        type: "uint256",
        indexed: false,
        internalType: "uint256",
      },
    ],
    anonymous: false,
  },
  {
    name: "OwnershipTransferred",
    type: "event",
    inputs: [
      {
        name: "previousOwner",
        type: "address",
        indexed: true,
        internalType: "address",
      },
      {
        name: "newOwner",
        type: "address",
        indexed: true,
        internalType: "address",
      },
    ],
    anonymous: false,
  },
  {
    name: "Transfer",
    type: "event",
    inputs: [
      { name: "from", type: "address", indexed: true, internalType: "address" },
      { name: "to", type: "address", indexed: true, internalType: "address" },
      {
        name: "value",
        type: "uint256",
        indexed: false,
        internalType: "uint256",
      },
    ],
    anonymous: false,
  },
  {
    name: "allowance",
    type: "function",
    inputs: [
      { name: "owner", type: "address", internalType: "address" },
      { name: "spender", type: "address", internalType: "address" },
    ],
    outputs: [{ name: "", type: "uint256", internalType: "uint256" }],
    stateMutability: "view",
  },
  {
    name: "approve",
    type: "function",
    inputs: [
      { name: "spender", type: "address", internalType: "address" },
      { name: "amount", type: "uint256", internalType: "uint256" },
    ],
    outputs: [{ name: "", type: "bool", internalType: "bool" }],
    stateMutability: "nonpayable",
  },
  {
    name: "balanceOf",
    type: "function",
    inputs: [{ name: "account", type: "address", internalType: "address" }],
    outputs: [{ name: "", type: "uint256", internalType: "uint256" }],
    stateMutability: "view",
  },
  {
    name: "burn",
    type: "function",
    inputs: [{ name: "amount", type: "uint256", internalType: "uint256" }],
    outputs: [],
    stateMutability: "nonpayable",
  },
  {
    name: "burn",
    type: "function",
    inputs: [
      { name: "account_", type: "address", internalType: "address" },
      { name: "value_", type: "uint256", internalType: "uint256" },
    ],
    outputs: [],
    stateMutability: "nonpayable",
  },
  {
    name: "burnFrom",
    type: "function",
    inputs: [
      { name: "account", type: "address", internalType: "address" },
      { name: "amount", type: "uint256", internalType: "uint256" },
    ],
    outputs: [],
    stateMutability: "nonpayable",
  },
  {
    name: "decimals",
    type: "function",
    inputs: [],
    outputs: [{ name: "", type: "uint8", internalType: "uint8" }],
    stateMutability: "view",
  },
  {
    name: "decreaseAllowance",
    type: "function",
    inputs: [
      { name: "spender", type: "address", internalType: "address" },
      { name: "subtractedValue", type: "uint256", internalType: "uint256" },
    ],
    outputs: [{ name: "", type: "bool", internalType: "bool" }],
    stateMutability: "nonpayable",
  },
  {
    name: "increaseAllowance",
    type: "function",
    inputs: [
      { name: "spender", type: "address", internalType: "address" },
      { name: "addedValue", type: "uint256", internalType: "uint256" },
    ],
    outputs: [{ name: "", type: "bool", internalType: "bool" }],
    stateMutability: "nonpayable",
  },
  {
    name: "mint",
    type: "function",
    inputs: [
      { name: "account_", type: "address", internalType: "address" },
      { name: "value_", type: "uint256", internalType: "uint256" },
    ],
    outputs: [],
    stateMutability: "nonpayable",
  },
  {
    name: "name",
    type: "function",
    inputs: [],
    outputs: [{ name: "", type: "string", internalType: "string" }],
    stateMutability: "view",
  },
  {
    name: "owner",
    type: "function",
    inputs: [],
    outputs: [{ name: "", type: "address", internalType: "address" }],
    stateMutability: "view",
  },
  {
    name: "renounceOwnership",
    type: "function",
    inputs: [],
    outputs: [],
    stateMutability: "nonpayable",
  },
  {
    name: "symbol",
    type: "function",
    inputs: [],
    outputs: [{ name: "", type: "string", internalType: "string" }],
    stateMutability: "view",
  },
  {
    name: "totalSupply",
    type: "function",
    inputs: [],
    outputs: [{ name: "", type: "uint256", internalType: "uint256" }],
    stateMutability: "view",
  },
  {
    name: "transfer",
    type: "function",
    inputs: [
      { name: "recipient", type: "address", internalType: "address" },
      { name: "amount", type: "uint256", internalType: "uint256" },
    ],
    outputs: [{ name: "", type: "bool", internalType: "bool" }],
    stateMutability: "nonpayable",
  },
  {
    name: "transferFrom",
    type: "function",
    inputs: [
      { name: "sender", type: "address", internalType: "address" },
      { name: "recipient", type: "address", internalType: "address" },
      { name: "amount", type: "uint256", internalType: "uint256" },
    ],
    outputs: [{ name: "", type: "bool", internalType: "bool" }],
    stateMutability: "nonpayable",
  },
  {
    name: "transferOwner",
    type: "function",
    inputs: [{ name: "newOwner_", type: "address", internalType: "address" }],
    outputs: [],
    stateMutability: "nonpayable",
  },
  {
    name: "transferOwnership",
    type: "function",
    inputs: [{ name: "newOwner", type: "address", internalType: "address" }],
    outputs: [],
    stateMutability: "nonpayable",
  },
  {
    name: "update",
    type: "function",
    inputs: [
      { name: "name_", type: "string", internalType: "string" },
      { name: "symbol_", type: "string", internalType: "string" },
    ],
    outputs: [],
    stateMutability: "nonpayable",
  },
] as const;

const thorSoloClient = ThorClient.at(THOR_URL, {
  isPollingEnabled: false,
});

const godMnemonic =
  "denial kitchen pet squirrel other broom bar gas better priority spoil cross";
const godPrivateKey = Mnemonic.toPrivateKey(godMnemonic.split(" "));
const godPublicKey = Secp256k1.derivePublicKey(godPrivateKey);
const godAddress = Address.ofPublicKey(godPublicKey).toString();

const senderAccount: { privateKey: string; address: string } = {
  privateKey: Hex.of(godPrivateKey).toString(),
  address: godAddress,
};

const provider = new VeChainProvider(
  // Thor client used by the provider
  thorSoloClient,

  // Internal wallet used by the provider (needed to call the getSigner() method)
  new ProviderInternalBaseWallet([
    {
      privateKey: HexUInt.of(senderAccount.privateKey).bytes,
      address: senderAccount.address,
    },
  ]),

  // Disable fee delegation (BY DEFAULT IT IS DISABLED)
  false,
);

async function seed() {
  console.log("🚀 Starting Seeding Process (Native SDK Mode)...");

  const thorClient = ThorClient.at(THOR_URL);

  const clauses: TransactionClause[] = [];

  console.log(`📝 Funding ${recipients.length} wallets...`);

  // Loop & Fund
  for (const recipient of recipients) {
    try {
      const VETclause = Clause.transferVET(
        Address.of(recipient.address),
        VET.of(100),
      ) as TransactionClause;

      clauses.push(VETclause);
    } catch (e) {
      console.error(`❌ Failed to fund ${recipient.address}:`, e);
      if (e instanceof Error) {
        console.error(`   Error message: ${e.message}`);
        if (e.stack) console.error(`   Stack: ${e.stack}`);
      }
    }
  }

  const gasResult = await thorSoloClient.gas.estimateGas(clauses);

  const txBody = await thorSoloClient.transactions.buildTransactionBody(
    clauses,
    gasResult.totalGas,
  );

  const signer = await provider.getSigner(senderAccount.address);

  const rawSignedTransaction = await signer!.signTransaction(
    signerUtils.transactionBodyToTransactionRequestInput(
      txBody,
      senderAccount.address,
    ),
  );

  const signedTransaction = Transaction.decode(
    HexUInt.of(rawSignedTransaction.slice(2)).bytes,
    true,
  );

  // 5 - Send the transaction
  const sendTransactionResult =
    await thorSoloClient.transactions.sendTransaction(signedTransaction);

  // 6 - Wait for transaction receipt
  const txReceipt = await thorSoloClient.transactions.waitForTransaction(
    sendTransactionResult.id,
  );

  console.log(txReceipt);

  console.log("🏁 Seeding Complete.");
}

seed().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});
