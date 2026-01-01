import ExecuteSmartContractButton from "./_components/ExecuteSmartContractButton";
import MetaMaskWalletButton from "./_components/MetaMaskWalletButton";

export default function Home() {
  return (
    <div className="">
      <MetaMaskWalletButton />
      <ExecuteSmartContractButton />
    </div>
  );
}
