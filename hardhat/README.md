# Batcher Smart Contract

Batch ETH transfer contract using Hardhat with Ethereum mainnet forking.

## Dependencies

| Package | Purpose |
|---------|---------|
| `hardhat` | Development environment |
| `@nomicfoundation/hardhat-toolbox` | Plugin bundle |
| `@vechain/sdk-hardhat-plugin` | VeChain support |
| `dotenv` | Environment variables |

## Forking

Uses Alchemy to fork Ethereum mainnet locally for testing against real mainnet state without spending real ETH. Configured in `hardhat.config.ts` via `ALCHEMY_MAINNET_URL`.

## Deployment

**Terminal 1:** Start local forked node
```bash
npx hardhat node
```

**Terminal 2:** Deploy contract
```bash
npx hardhat ignition deploy ignition/modules/Batcher.ts --network localhost
```

Deployment address saved to `ignition/deployments/chain-31337/deployed_addresses.json`.

## Commands

```bash
npx hardhat compile              # Compile contracts
npx hardhat test                 # Run tests
npx hardhat clean                # Clean artifacts
```
