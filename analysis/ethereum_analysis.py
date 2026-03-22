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
    import ssl
    from datetime import datetime, timedelta

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    date = datetime.strptime(api_date, "%Y%m%d")
    for _ in range(30):
        url = DIGICONOMIST_API_TEMPLATE.format(date=date.strftime("%Y%m%d"))
        with urllib.request.urlopen(url, timeout=10, context=ctx) as response:
            payload = json.loads(response.read().decode("utf-8"))
        if payload and "Gas_unit_gCO2" in payload[0]:
            return float(payload[0]["Gas_unit_gCO2"])
        date -= timedelta(days=1)

    raise ValueError(f"Gas_unit_gCO2 not found in API for {api_date} or the 30 preceding days")


def plot_metric_lines_by_throughput(df, metric_column, y_label, title_prefix, scale=1.0):
    throughputs = sorted(df["throughput"].dropna().unique())

    for throughput in throughputs:
        subset = df[df["throughput"] == throughput].copy()
        intervals = sorted(subset["batchIntervalMinutes"].dropna().unique())

        for interval in intervals:
            interval_df = subset[subset["batchIntervalMinutes"] == interval].copy()
            interval_df = interval_df.sort_values("batchSize")

            values = interval_df[metric_column] / scale
            avg = values.mean()

            fig, ax = plt.subplots(figsize=(9, 4))
            ax.plot(interval_df["batchSize"], values, marker="o", linewidth=2)
            ax.axhline(avg, color="red", linestyle="--", linewidth=1.2)
            ax.text(0.02, 0.98, f"Avg: {avg:.2f}", transform=ax.transAxes,
                    va="top", ha="left", color="red", fontsize=9)
            ax.set_title(f"{title_prefix} — Throughput={throughput}, Batch Interval={interval} min")
            ax.set_xlabel("Batch Size")
            ax.set_ylabel(y_label)
            ax.set_xticks(interval_df["batchSize"])
            ax.set_yticks(sorted(values.tolist()))
            ax.yaxis.set_major_formatter(plt.FormatStrFormatter("%.2f"))
            ax.tick_params(axis="x", rotation=45)
            ax.grid(True, alpha=0.3)
            fig.tight_layout()

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

            batch_numbers = sorted(b["batchNumber"] for b in data.get("batches", []) if "batchNumber" in b)
            if not batch_numbers or batch_numbers[0] != 1 or any(batch_numbers[i+1] - batch_numbers[i] > 1 for i in range(len(batch_numbers) - 1)):
                print(f"  [SKIP] {filename}: batch numbers are not sequential or do not start from 1")
                continue

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
            co2_saved_g  = gas_result["gasSaved"] * gas_unit_gco2

            merged = {
                "file": filename,
                **shared,
                **gas_result,
                "gasUnitgCO2": round(gas_unit_gco2, 12),
                "co2SavedKg": round(co2_saved_kg, 4),
                "co2SavedG": round(co2_saved_g, 4),
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
        "totalIndividualGasUsed", "totalBatchGasUsed", "gasSaved", "percentageSaved", "gasUnitgCO2", "co2SavedKg", "co2SavedG",
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
        metric_column="co2SavedKg",
        y_label="Carbon Saved (kg CO₂)",
        title_prefix="Carbon Savings vs Batch Size",
    )

    plot_metric_lines_by_throughput(
        df=df,
        metric_column="percentageSaved",
        y_label="Carbon Emission Reduction (%)",
        title_prefix="Carbon Emission Reduction % vs Batch Size",
    )

    plot_metric_lines_by_throughput(
        df=df,
        metric_column="avgLatencyMs",
        y_label="Average Latency (s)",
        title_prefix="Average Latency vs Batch Size",
        scale=1000,
    )

    plt.show()

if __name__ == "__main__":
    main()