# Final Year Project

This project contains three parts:

- `hardhat/` for Ethereum contract deployment and local testing
- `off-chain/` for the simulations and supporting scripts
- `analysis/` for the Python analysis scripts and result files

## Prerequisites

- Node.js installed
- npm installed
- Docker installed and running

## Simulation options

You can run the project in two ways:

1. Main project simulations (script-based)
2. Presentation simulation (frontend UI)

## Step 3: Start shared setup (before any simulation)

Run these in separate terminals before starting Option 1 or Option 2:

1. Open a terminal in the project root folder and run the prep scripts:

	```bash
	npm run ETHprep
	npm run VETprep
	```

2. Open a terminal in the `hardhat/` folder and start the Hardhat node:

	```bash
	npx hardhat node
	```

3. Open Docker Desktop, then start the VeChain Thor solo node in another terminal:

	```bash
	docker run -p 127.0.0.1:8669:8669 vechain/thor:latest solo --api-allowed-tracers all --api-cors '*' --api-addr 0.0.0.0:8669
	```

## Option 1: Run the main project simulations (script-based)

The main simulations are the TypeScript scripts in `off-chain/simulation/`:

- `EthereumUSDCSimulation.ts`
- `VeChainUSDCSimulation.ts`

Before running the scripts, create the log folders (if they do not exist):

```bash
mkdir -p simulation/EthereumSimulationLogs simulation/VeChainSimulationLogs
```

After completing Step 3, run from `off-chain/`:

```bash
npx tsx simulation/EthereumUSDCSimulation.ts
npx tsx simulation/VeChainUSDCSimulation.ts
```

Simulation logs are written to:

- `off-chain/simulation/EthereumSimulationLogs/`
- `off-chain/simulation/VeChainSimulationLogs/`

## Option 2: Run the presentation simulation (frontend UI)

After completing Step 3, start the off-chain app from the `off-chain/` folder:

1. Start the app:

	```bash
	npm install
	npm run dev
	```

2. Open the app in your browser and use the simulation from the UI.

## Useful commands

### Hardhat

```bash
cd hardhat
npx hardhat compile
npx hardhat test
```

### Off-chain app

```bash
cd off-chain
npm run dev
npm run build
```

### Analysis scripts

```bash
cd analysis
python ethereum_analysis.py
python vechain_analysis.py
```
