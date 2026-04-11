import sys
import os
import json
import glob
import re
from datetime import date
import pandas as pd
import matplotlib.pyplot as plt
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
API_KEY = os.getenv("API_KEY")


def _get_api_headers() -> dict:
    if not API_KEY:
        raise RuntimeError("Missing API_KEY. Add it to analysis/.env or project-root .env")
    return {"X-API-Key": API_KEY}


def fetch_daily_emission(day: str) -> dict:
    """Fetch network CO2e emission for a specific day (YYYY-MM-DD)."""
    resp = requests.get(
        "https://api.vechainstats.com/v2/carbon/co2e-network",
        params={"timeframe": day},
        headers=_get_api_headers(),
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def fetch_daily_gas_stats(day: str) -> dict:
    """Fetch network gas limit/used stats for a specific day (YYYY-MM-DD)."""
    resp = requests.get(
        "https://api.vechainstats.com/v2/network/gas-stats",
        params={"timeframe": day},
        headers=_get_api_headers(),
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def _to_float(value):
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.strip().replace(",", "")
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None


def _extract_first_numeric(payload, key_hints):
    """Find the first numeric value in nested JSON where key matches a hint."""
    queue = [payload]
    hints = [h.lower() for h in key_hints]

    while queue:
        current = queue.pop(0)

        if isinstance(current, dict):
            for key, value in current.items():
                key_l = str(key).lower()
                numeric = _to_float(value)
                if numeric is not None and any(h in key_l for h in hints):
                    return numeric
                if isinstance(value, (dict, list)):
                    queue.append(value)
        elif isinstance(current, list):
            queue.extend(current)

    return None


def get_today_gas_to_carbon_factor():
    """Get today's network-level CO2e per gas used for VeChain."""
    day = date.today().isoformat()
    emission_payload = fetch_daily_emission(day)
    gas_payload = fetch_daily_gas_stats(day)

    co2e_total = _extract_first_numeric(
        emission_payload,
        ["co2e", "co2", "carbon", "emission"],
    )
    gas_used_total = _extract_first_numeric(
        gas_payload,
        ["gasused", "gas_used", "usedgas", "totalgasused", "gas"],
    )

    if co2e_total is None:
        raise RuntimeError(f"Could not find CO2e value in emission response for {day}")
    if gas_used_total is None or gas_used_total <= 0:
        raise RuntimeError(f"Could not find positive gas-used value in gas response for {day}")

    return day, (co2e_total / gas_used_total), emission_payload, gas_payload

sys.path.insert(0, os.path.dirname(__file__))
from modules.gas_analysis import analyse_gas
from modules.latency_analysis import analyse_latency

VECHAIN_LOGS_PATH = os.path.join(
    os.path.dirname(__file__),
    "..", "off-chain", "simulation", "VeChainSimulationLogs"
)
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "results", "vechain_results.csv")


def load_json(path):
    with open(path, "r") as f:
        return json.load(f)


def print_header(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def plot_co2_grouped_bar(df):
    """Grouped bar chart: Unbatched vs Optimised CO2e emissions per throughput level."""
    throughputs = sorted(df["throughput"].dropna().unique())

    unbatched = []
    batched = []

    for t in throughputs:
        subset = df[df["throughput"] == t]
        best = subset.loc[subset["gasSaved"].idxmax()]
        unbatched.append(best["totalIndividualCO2e"])
        batched.append(best["totalBatchCO2e"])

    x = range(len(throughputs))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 6))
    bars1 = ax.bar([i - width / 2 for i in x], unbatched, width, label="Unbatched Baseline CO₂", color="tab:red", alpha=0.8)
    bars2 = ax.bar([i + width / 2 for i in x], batched, width, label="Optimised Batching CO₂", color="tab:green", alpha=0.8)

    ax.set_xlabel("Throughput (tx/s)")
    ax.set_ylabel("CO2e Emissions (network-derived units)")
    ax.set_title("Unbatched vs Optimised Batching CO₂ by Throughput (2-Hour Simulations)")
    ax.set_xticks(list(x))
    ax.set_xticklabels([f"T={t}" for t in throughputs])
    ax.legend()
    ax.bar_label(bars1, fmt="%.2f", padding=3, fontsize=8)
    ax.bar_label(bars2, fmt="%.2f", padding=3, fontsize=8)
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()


def plot_pareto_front(df):
    """Scatter plot of Latency vs CO2e Saved — Pareto Front."""
    fig, ax = plt.subplots(figsize=(10, 6))
    throughputs = sorted(df["throughput"].dropna().unique())
    colors = plt.cm.tab10.colors

    for i, throughput in enumerate(throughputs):
        subset = df[df["throughput"] == throughput]
        x = subset["avgLatencyMs"] / 1000
        y = subset["co2Saved"]
        ax.scatter(x, y, label=f"T={throughput}", color=colors[i % len(colors)], s=80, zorder=3)
        for _, row in subset.iterrows():
            ax.annotate(f"B={int(row['batchSize'])}", (row["avgLatencyMs"] / 1000, row["co2Saved"]),
                        textcoords="offset points", xytext=(6, 4), fontsize=7)

    ax.set_xlabel("Average Latency (s)")
    ax.set_ylabel("CO₂ Saved (network-derived units)")
    ax.set_title("Pareto Front: Latency vs CO₂ Savings")
    ax.legend(title="Throughput")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()


def plot_pareto_front_pct(df):
    """Scatter plot of Latency vs % Carbon Saved — Pareto Front."""
    fig, ax = plt.subplots(figsize=(10, 6))
    throughputs = sorted(df["throughput"].dropna().unique())
    colors = plt.cm.tab10.colors

    for i, throughput in enumerate(throughputs):
        subset = df[df["throughput"] == throughput]
        x = subset["avgLatencyMs"] / 1000
        y = subset["percentageSaved"]
        ax.scatter(x, y, label=f"T={throughput}", color=colors[i % len(colors)], s=80, zorder=3)
        for _, row in subset.iterrows():
            ax.annotate(f"B={int(row['batchSize'])}", (row["avgLatencyMs"] / 1000, row["percentageSaved"]),
                        textcoords="offset points", xytext=(6, 4), fontsize=7)

    ax.set_xlabel("Average Latency (s)")
    ax.set_ylabel("Carbon Emission Reduction (%)")
    ax.set_title("Pareto Front: Latency vs Carbon Emission Reduction % (2-Hour Simulations)")
    ax.legend(title="Throughput")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()


def plot_latency_boxplot(json_files):
    """Violin plots of transaction latency per batch size, split by throughput."""
    from collections import defaultdict
    data_map = defaultdict(lambda: defaultdict(list))

    for json_file in json_files:
        with open(json_file) as f:
            data = json.load(f)
        batch_size = data.get("batchSize")
        throughput = data.get("throughput")
        if batch_size is None or throughput is None:
            continue
        for batch in data.get("batches", []):
            batch_ts = batch.get("timestamp")
            if batch_ts is None:
                continue
            for tx in batch.get("transactions", []):
                tx_ts = tx.get("timeStamp")
                if tx_ts is not None:
                    data_map[throughput][batch_size].append((batch_ts - tx_ts) / 1000)

    if not data_map:
        return

    throughputs = sorted(data_map)
    fig, axes = plt.subplots(1, len(throughputs), figsize=(6 * len(throughputs), 6), sharey=True)
    if len(throughputs) == 1:
        axes = [axes]

    for ax, throughput in zip(axes, throughputs):
        sorted_sizes = sorted(data_map[throughput])
        ax.violinplot(
            [data_map[throughput][s] for s in sorted_sizes],
            positions=range(len(sorted_sizes)),
            showmeans=True,
            showmedians=True,
        )
        ax.set_title(f"Throughput = {throughput}")
        ax.set_xlabel("Batch Size")
        ax.set_xticks(range(len(sorted_sizes)))
        ax.set_xticklabels(sorted_sizes)
        ax.grid(True, axis="y", alpha=0.3)

    axes[0].set_ylabel("Transaction Latency (s)")
    fig.suptitle("Transaction Latency Distribution by Batch Size")
    fig.tight_layout()


def plot_metric_lines_by_throughput(df, metric_column, y_label, title_prefix, scale=1.0):
    throughputs = sorted(df["throughput"].dropna().unique())

    for throughput in throughputs:
        subset = df[df["throughput"] == throughput].copy()
        intervals = sorted(subset["batchIntervalMinutes"].dropna().unique())

        for interval in intervals:
            interval_df = subset[subset["batchIntervalMinutes"] == interval].copy()
            interval_df = interval_df.sort_values("batchSize")

            fig, ax = plt.subplots(figsize=(10, 4))
            values = interval_df[metric_column] / scale
            avg = values.mean()
            ax.plot(interval_df["batchSize"], values, marker="o", linewidth=2)
            ax.axhline(avg, color="red", linestyle="--", linewidth=1.2)
            ax.text(0.02, 0.98, f"Avg: {avg:.2f}", transform=ax.transAxes, va="top", ha="left", color="red", fontsize=9)
            ax.set_ylabel(y_label)
            ax.set_yticks(sorted(values.tolist()))
            ax.yaxis.set_major_formatter(plt.FormatStrFormatter("%.2f"))
            ax.set_title(f"{title_prefix} — Throughput={throughput}, Batch Interval={interval} min")
            ax.set_xlabel("Batch Size")
            ax.set_xticks(interval_df["batchSize"])
            ax.tick_params(axis="x", rotation=45)
            ax.grid(True, alpha=0.3)
            fig.tight_layout()


def print_summary_table(df):
    print_header("Independent Variables vs Numerical Outputs")
    cols = {
        "Throughput": "throughput",
        "Batch Interval (min)": "batchIntervalMinutes",
        "Batch Size": "batchSize",
        "Total Gas Used": "totalBatchGasUsed",
        "Gas Saved": "gasSaved",
        "CO₂ Saved": "co2Saved",
        "% Saved": "percentageSaved",
        "Mean Latency (ms)": "avgLatencyMs",
        "Max Latency (ms)": "maxLatencyMs",
    }
    table = df[[v for v in cols.values() if v in df.columns]].copy()
    table = table.sort_values(["throughput", "batchIntervalMinutes", "batchSize"])
    table.columns = [k for k, v in cols.items() if v in df.columns]
    print(table.to_string(index=False, float_format=lambda x: f"{x:.2f}"))


def main():
    logs_dir = os.path.abspath(VECHAIN_LOGS_PATH)

    if not os.path.isdir(logs_dir):
        print(f"Error: Could not find logs directory at:\n  {logs_dir}")
        sys.exit(1)

    json_files = sorted(glob.glob(os.path.join(logs_dir, "*.json")))

    if not json_files:
        print(f"No JSON files found in: {logs_dir}")
        sys.exit(1)

    print_header("VeChain Gas & Latency Analysis")
    print(f"  Found {len(json_files)} log file(s)\n")

    try:
        factor_day, gas_to_carbon_factor, emission_payload, gas_payload = get_today_gas_to_carbon_factor()
        print(f"  Using gas->CO2e factor for {factor_day}: {gas_to_carbon_factor:.12f}")
    except Exception as e:
        print(f"Error: Could not derive gas->CO2e factor from VeChain APIs: {e}")
        sys.exit(1)

    rows = []

    for json_file in json_files:
        filename = os.path.basename(json_file)
        print(f"  Processing: {filename}")

        try:
            data = load_json(json_file)

            batch_numbers = sorted(b["batchNumber"] for b in data.get("batches", []) if "batchNumber" in b)
            if not batch_numbers or batch_numbers[0] != 1 or any(batch_numbers[i+1] - batch_numbers[i] > 1 for i in range(len(batch_numbers) - 1)):
                print(f"  [SKIP] {filename}: batch numbers are not sequential or do not start from 1")
                continue

            gas_result = analyse_gas(data)
            latency_result = analyse_latency(data)

            rows.append({
                "file": filename,
                "batchSize": data["batchSize"],
                "batchIntervalMinutes": data["batchIntervalMinutes"],
                "throughput": data["throughput"],
                **gas_result,
                "vechainApiDateUsed": factor_day,
                "vechainEmissionApiResponse": json.dumps(emission_payload, separators=(",", ":")),
                "vechainGasApiResponse": json.dumps(gas_payload, separators=(",", ":")),
                "gasToCarbonFactor": gas_to_carbon_factor,
                "totalIndividualCO2e": gas_result["totalIndividualGasUsed"] * gas_to_carbon_factor,
                "totalBatchCO2e": gas_result["totalBatchGasUsed"] * gas_to_carbon_factor,
                "co2Saved": gas_result["gasSaved"] * gas_to_carbon_factor,
                **latency_result,
            })

        except Exception as e:
            print(f"  [WARN] Skipping {filename}: {e}")

    if not rows:
        print("No data processed. Exiting.")
        sys.exit(1)

    df = pd.DataFrame(rows)

    col_order = [
        "file", "batchSize", "batchIntervalMinutes", "throughput",
        "totalIndividualGasUsed", "totalBatchGasUsed", "gasSaved", "percentageSaved",
        "vechainApiDateUsed", "vechainEmissionApiResponse", "vechainGasApiResponse",
        "gasToCarbonFactor", "totalIndividualCO2e", "totalBatchCO2e", "co2Saved",
        "avgLatencyMs", "minLatencyMs", "maxLatencyMs", "totalTransactionsAnalysed",
    ]
    df = df[[c for c in col_order if c in df.columns]]

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)

    print_header("Summary")
    print(df.to_string(index=False, float_format=lambda x: f"{x:.2f}"))
    print(f"\n✅ Results saved to: {OUTPUT_PATH}")

    print_summary_table(df)

    plot_metric_lines_by_throughput(df, "co2Saved", "CO₂ Saved", "Carbon Savings vs Batch Size (2-Hour Simulations)")
    plot_metric_lines_by_throughput(df, "percentageSaved", "Carbon Emission Reduction (%)", "Carbon Emission Reduction % vs Batch Size")
    plot_metric_lines_by_throughput(df, "avgLatencyMs", "Average Latency (s)", "Average Latency vs Batch Size", scale=1000)

    processed_files = [r["file"] for r in rows]
    plot_latency_boxplot([f for f in json_files if os.path.basename(f) in processed_files])

    plot_pareto_front(df)
    plot_pareto_front_pct(df)
    plot_co2_grouped_bar(df)

    plt.show()


if __name__ == "__main__":
    main()
