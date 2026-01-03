import { buildModule } from "@nomicfoundation/hardhat-ignition/modules";

const BatcherModule = buildModule("BatcherModule", (m) => {
  const batcher = m.contract("Batcher");

  return { batcher };
});

export default BatcherModule;