import { Secp256k1, Address } from "@vechain/sdk-core";
import * as fs from "fs";
import * as path from "path";

const WALLET_COUNT = 150;

async function generateWallets() {
  console.log(`Generating ${WALLET_COUNT} VeChain wallets...`);
  const wallets = [];

  for (let i = 0; i < WALLET_COUNT; i++) {
    // Generate random private key
    const privateKey = await Secp256k1.generatePrivateKey();
    const publicKey = await Secp256k1.derivePublicKey(privateKey);
    const address = await Address.ofPublicKey(publicKey);

    wallets.push({
      id: i + 1,
      address: `${address.toString()}`,
      privateKey: `0x${Buffer.from(privateKey).toString("hex")}`,
    });

    if ((i + 1) % 10 === 0) {
      console.log(`Generated ${i + 1}/${WALLET_COUNT} wallets...`);
    }
  }

  const outDir = path.join(process.cwd(), "lib");
  if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });

  const outFile = path.join(outDir, "vechain-wallets.json");
  fs.writeFileSync(outFile, JSON.stringify(wallets, null, 2));

  console.log(`✅ Generated and saved ${wallets.length} wallets to ${outFile}`);
}

generateWallets().catch(console.error);
