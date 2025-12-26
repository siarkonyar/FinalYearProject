pragma solidity ^0.8.28;

contract MyContract {
    event BatchExecuted(
        uint256 batchSize,
        uint256 totalAmount,
        uint256 gasUsed
    );
    event TransferExecuted(
        address indexed recipient,
        uint256 amount,
        uint256 gasUsed
    );

    //TODO: add only backend can call this contract things
    address private immutable backend;
    constructor() {
        backend = msg.sender;
    }

    modifier onlyBackend() {
        require(msg.sender == backend, "Not authorized");
        _;
    }

    function executeBatch(
        address[] calldata recipients,
        uint256[] calldata amounts
    ) external payable onlyBackend {
        uint256 batchGasStart = gasleft(); // it's accurate enough for monitoring/analytics and uses gas itself,
        // Check transaction receipt after execution (free, but only total gas):
        /*
        const tx = await contract.executeBatch(recipients, amounts, { value: total });
        const receipt = await tx.wait();
        console.log("Gas used:", receipt.gasUsed.toString());
         */
        /*
        What Gets Included?

        -Validation logic gas
        -Loop overhead gas
        -Actual transfer gas
        -Event emission gas */
        require(recipients.length == amounts.length, "Arrays length mismatch");
        require(recipients.length > 0, "Empty batch");

        uint256 totalAmount = 0;

        // TODO: find and alternative for for loops because they use much gas
        for (uint i = 0; i < amounts.length; i++) {
            totalAmount += amounts[i];
        }

        require(msg.value == totalAmount, "Incorrect ETH sent");

        for (uint256 i = 0; i < recipients.length; i++) {
            uint256 gasStart = gasleft();
            (bool success, ) = recipients[i].call{value: amounts[i]}(""); //didnt understand this for loop. how it works?
            uint256 gasUsed = gasStart - gasleft();
            require(success, "transaction failed"); //returns all ETH to sender (backend)
            emit TransferExecuted(recipients[i], amounts[i], gasUsed);
        }

        uint256 batchGasUsed = batchGasStart - gasleft();

        emit BatchExecuted(recipients.length, totalAmount, batchGasUsed);
    }
}
