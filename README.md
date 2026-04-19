# Final Year Project

Compares Ethereum and VeChain USDC batch transaction performance via on-chain simulations.

## Project structure

| Folder | Purpose |
|---|---|
| `hardhat/` | Ethereum contract deployment and local testing |
| `off-chain/` | Simulation scripts and frontend UI |
| `analysis/` | Python analysis scripts and result files |

## Prerequisites

- Node.js v18+ and npm
- Docker Desktop
- Python 3

## Environment setup

Each sub-project needs a `.env` file before running anything.

**`hardhat/.env`**
```env
ALCHEMY_MAINNET_URL="https://eth-mainnet.g.alchemy.com/v2/<your-api-key>"
USDC_ADDRESS=<deployed USDC contract address>
```

**`off-chain/.env`**
```env
NEXT_PUBLIC_ETHEREUM_BATCHER_ADDRESS="<deployed Ethereum batcher address>"
NEXT_PUBLIC_VECHAIN_BATCHER_ADDRESS="<deployed VeChain batcher address>"
NEXT_PUBLIC_VECHAIN_USDC_ADDRESS="<deployed VeChain USDC address>"

NEXT_PUBLIC_SIMULATION_BATCH_SIZE=125
NEXT_PUBLIC_SIMULATION_BATCH_INTERVAL_MIN=5
NEXT_PUBLIC_SIMULATION_DURATION_MIN=120
NEXT_PUBLIC_TARGET_TPS=9
```

**`analysis/.env`**
```env
API_KEY=<your VeChain Stats API key>
```

## Running the simulations

### 1. Shared setup (required for both options)

**Step 1 — Install dependencies:**
```bash
# Root
npm install --legacy-peer-deps

# Off-chain
cd off-chain && npm install --legacy-peer-deps
```

**Step 2 — Start the Hardhat node** (keep this terminal open):
```bash
cd hardhat
npx hardhat node
```

**Step 3 — Start the VeChain Thor solo node** (keep this terminal open):
```bash
docker run -p 127.0.0.1:8669:8669 vechain/thor:latest solo --api-allowed-tracers all --api-cors '*' --api-addr 0.0.0.0:8669
```

**Step 4 — Run preparation scripts** (from the root, in a new terminal):

Each script deploys the contracts, funds the wallets, and approves the batcher — everything needed before running a simulation.
```bash
npm run ETHprep
npm run VETprep
```

### 2a. Script-based simulation

From `off-chain/`, create the log folders if they don't exist:
```bash
mkdir -p simulation/EthereumSimulationLogs simulation/VeChainSimulationLogs
```

Then run the simulations:
```bash
npx tsx simulation/EthereumUSDCSimulation.ts
npx tsx simulation/VeChainUSDCSimulation.ts
```

Logs are written to `off-chain/simulation/EthereumSimulationLogs/` and `off-chain/simulation/VeChainSimulationLogs/`.

### 2b. Frontend simulation

From `off-chain/`:
```bash
npm run dev
```

Open the app in a browser and run the simulation from the UI.

## Analysis

```bash
cd analysis
pip install -r requirements.txt
python ethereum_analysis.py
python vechain_analysis.py
```

## Other useful commands

```bash
# Hardhat
cd hardhat && npx hardhat compile
cd hardhat && npx hardhat test

# Off-chain app
cd off-chain && npm run build
```

## Troubleshooting

**Prep scripts fail immediately** — the Hardhat node and Docker Thor node must both be running before executing `npm run ETHprep` / `npm run VETprep`.

**`npx tsx` not found** — run `npm install --legacy-peer-deps` inside `off-chain/` first.

**VeChain deploy fails** — confirm the Thor container is running and accessible at `http://localhost:8669`.

## Packages

<details>
<summary>Hardhat</summary>

**Dev:** `hardhat`, `@nomicfoundation/hardhat-toolbox`, `@vechain/sdk-hardhat-plugin`

**Runtime:** `@tenderly/hardhat-tenderly`, `dotenv`

</details>

<details>
<summary>Off-chain</summary>

**Runtime:** `next`, `react`, `react-dom`, `ethers`, `viem`, `wagmi`, `@metamask/sdk`, `@tanstack/react-query`, `@vechain/sdk-core`, `@vechain/sdk-network`, `dotenv`, `jsdom`

**Dev:** `typescript`, `eslint`, `eslint-config-next`, `tailwindcss`, `@tailwindcss/postcss`, `@types/node`, `@types/react`, `@types/react-dom`, `@testing-library/react`, `@testing-library/dom`, `@testing-library/react-hooks`

</details>

<details>
<summary>Analysis (Python)</summary>

`pandas`, `matplotlib`, `requests`, `python-dotenv`

</details>

## Project Report

The full project report is available here: [Project-report.pdf](Project-report.pdf).
