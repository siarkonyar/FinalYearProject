def analyse_gas(data):
    batch_size = data["batchSize"]
    batch_interval = data["batchIntervalMinutes"]
    throughput = data["throughput"]

    # Collect all timestamps present across all batches
    batch_timestamps = set()
    for batch in data.get("batches", []):
        for tx in batch.get("transactions", []):
            ts = tx.get("timeStamp")
            if ts is not None:
                batch_timestamps.add(ts)

    # Only sum gas for individual transactions whose timestamp exists in a batch
    total_individual = sum(
        int(tx["gasUsed"])
        for tx in data.get("individualTransactions", [])
        if tx.get("timestamp") in batch_timestamps
    )

    total_batch = int(data["summary"]["totalBatchGasUsed"])

    gas_saved = total_individual - total_batch
    percentage_saved = (gas_saved / total_individual * 100) if total_individual > 0 else 0

    return {
        "totalIndividualGasUsed": total_individual,
        "totalBatchGasUsed": total_batch,
        "gasSaved": gas_saved,
        "percentageSaved": round(percentage_saved, 2),
    }