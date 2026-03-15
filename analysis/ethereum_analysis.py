import sys
import os
import json
import glob
import re
import urllib.request
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(__file__))

from modules.gas_analysis import analyse_gas
from modules.latency_analysis import analyse_latency

def load_json(path):
    with open(path, "r") as f:
        return json.load(f)

def print_header(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

ETHEREUM_LOGS_PATH = os.path.join(
    os.path.dirname(__file__),
    "..", "off-chain", "simulation", "EthereumSimulationLogs"
)

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "results", "ethereum_results.csv")
DIGICONOMIST_API_TEMPLATE = "https://digiconomist.net/wp-json/mo/v1/ethereum/stats/{date}"


def extract_api_date_from_filename(filename):
    match = re.search(r"(\d{4})-(\d{2})-(\d{2})T", filename)
    if not match:
        raise ValueError("Could not parse date from filename")
    return "".join(match.groups())


def fetch_gas_unit_gco2(api_date):
    url = DIGICONOMIST_API_TEMPLATE.format(date=api_date)
    with urllib.request.urlopen(url, timeout=10) as response:
        payload = json.loads(response.read().decode("utf-8"))

    if not payload or "Gas_unit_gCO2" not in payload[0]:
        raise ValueError("Gas_unit_gCO2 missing in API response")

    return float(payload[0]["Gas_unit_gCO2"])


def plot_metric_lines_by_throughput(df, metric_column, y_label, title_prefix):
    throughputs = sorted(df["throughput"].dropna().unique())

    for throughput in throughputs:
        subset = df[df["throughput"] == throughput].copy()
        intervals = sorted(subset["batchIntervalMinutes"].dropna().unique())

        if not intervals:
            continue

        fig, axes = plt.subplots(
            nrows=len(intervals),
            ncols=1,
            figsize=(9, 4 * len(intervals)),
            squeeze=False,
        )

        for idx, interval in enumerate(intervals):
            interval_df = subset[subset["batchIntervalMinutes"] == interval].copy()
            interval_df = interval_df.sort_values("batchSize")

            ax = axes[idx][0]
            ax.plot(
                interval_df["batchSize"],
                interval_df[metric_column],
                marker="o",
                linewidth=2,
            )

            ax.set_title(f"Throughput={throughput}, Batch Interval={interval} min")
            ax.set_xlabel("Batch Size")
            ax.set_ylabel(y_label)
            ax.grid(True, alpha=0.3)

        fig.suptitle(f"{title_prefix} (Throughput={throughput})", fontsize=14)
        fig.tight_layout(rect=[0, 0, 1, 0.97])

def main():
    logs_dir = os.path.abspath(ETHEREUM_LOGS_PATH)

    if not os.path.isdir(logs_dir):
        print(f"Error: Could not find logs directory at:\n  {logs_dir}")
        sys.exit(1)

    json_files = sorted(glob.glob(os.path.join(logs_dir, "*.json")))

    if not json_files:
        print(f"No JSON files found in: {logs_dir}")
        sys.exit(1)

    print_header("Ethereum Gas & Latency Analysis")
    print(f"  Found {len(json_files)} log file(s)\n")

    rows = []
    gco2_cache = {}

    for json_file in json_files:
        filename = os.path.basename(json_file)
        print(f"  Processing: {filename}")

        try:
            data = load_json(json_file)
            api_date = extract_api_date_from_filename(filename)

            if api_date not in gco2_cache:
                gco2_cache[api_date] = fetch_gas_unit_gco2(api_date)

            gas_unit_gco2 = gco2_cache[api_date]

            shared = {
                "batchSize": data["batchSize"],
                "batchIntervalMinutes": data["batchIntervalMinutes"],
                "throughput": data["throughput"],
            }

            gas_result     = analyse_gas(data)
            latency_result = analyse_latency(data)
            co2_saved_kg = (gas_result["gasSaved"] * gas_unit_gco2) / 1000

            merged = {
                "file": filename,
                **shared,
                **gas_result,
                "gasUnitgCO2": round(gas_unit_gco2, 12),
                "co2SavedKg": round(co2_saved_kg, 4),
                **latency_result,
            }

            rows.append(merged)

        except Exception as e:
            print(f"  [WARN] Skipping {filename}: {e}")

    if not rows:
        print("No data processed. Exiting.")
        sys.exit(1)

    df = pd.DataFrame(rows)

    col_order = [
        "file", "batchSize", "batchIntervalMinutes", "throughput",
        "totalIndividualGasUsed", "totalBatchGasUsed", "gasSaved", "percentageSaved", "gasUnitgCO2", "co2SavedKg",
        "avgLatencyMs", "minLatencyMs", "maxLatencyMs", "totalTransactionsAnalysed",
    ]
    df = df[[c for c in col_order if c in df.columns]]

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)

    print_header("Summary")
    print(df.to_string(index=False))
    print(f"\n✅ Results saved to: {OUTPUT_PATH}")

    plot_metric_lines_by_throughput(
        df=df,
        metric_column="gasSaved",
        y_label="Gas Saved",
        title_prefix="Gas Savings vs Batch Size",
    )

    plot_metric_lines_by_throughput(
        df=df,
        metric_column="avgLatencyMs",
        y_label="Average Latency (ms)",
        title_prefix="Average Latency vs Batch Size",
    )

    plt.show()

if __name__ == "__main__":
    main()