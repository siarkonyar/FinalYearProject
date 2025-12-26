import { ethers } from "hardhat";
async function main() {
  const [deployer] = await ethers.getSigners();
  console.log("Deploying with:", deployer.address);
  const ContractFactory = await ethers.getContractFactory("MyContract");
  const contract = await ContractFactory.deploy();
  console.log("Contract deployed at:", contract.target);
}
main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
