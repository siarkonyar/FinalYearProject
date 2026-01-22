export type Transaction = {
  sender: `0x${string}`;
  recipient: `0x${string}`;
  amount: bigint;
  senderPrivateKey?: `0x${string}`;
};

export interface IndividualTxLog {
  txHash: string;
  sender: string;
  recipient: string;
  amount: string;
  gasUsed: string;
  blockNumber: number | null;
  timestamp: number;
}

export interface BatchLog {
  batchNumber: number;
  txHash: string;
  gasUsed: string;
  blockNumber: number | null;
  timestamp: number;
  transactionCount: number;
  transactions: Array<{
    sender: string;
    recipient: string;
    amount: string;
  }>;
}

export interface SimulationLog {
  simulationStartTime: number;
  simulationEndTime: number;
  simulationDuration: number;
  batchSize: number;
  batchIntervalMinutes: number;
  individualTransactions: IndividualTxLog[];
  batches: BatchLog[];
  summary: {
    totalIndividualTransactions: number;
    totalBatches: number;
    totalIndividualGasUsed: string;
    totalBatchGasUsed: string;
  };
}