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

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
CO2_CSV_PATH = os.path.join(DATA_DIR, "ethereum-daily-co2.csv")
GAS_CSV_PATH = os.path.join(DATA_DIR, "ethereum-daily-gas.csv")

def load_csv_gas_unit_gco2():
    """
    Derives Gas_unit_gCO2 from CSV data by dividing daily estimated CO2
    (KtCO2e → gCO2) by daily total gas used, then returns a date-indexed Series.
    """
    co2_df = pd.read_csv(CO2_CSV_PATH, parse_dates=["Date and Time"])
    co2_df = co2_df.rename(columns={"Date and Time": "date"})
    co2_df["date"] = co2_df["date"].dt.normalize()

    gas_df = pd.read_csv(GAS_CSV_PATH)
    gas_df["date"] = pd.to_datetime(gas_df["Date(UTC)"]).dt.normalize()

    merged = pd.merge(co2_df[["date", "Estimated, KtCO2e"]], gas_df[["date", "Value"]], on="date")
    # KtCO2e * 1e7 = gCO2 (empirically matched to Digiconomist unit); divide by daily gas to get gCO2 per gas unit
    merged["gas_unit_gco2_csv"] = (merged["Estimated, KtCO2e"] * 1e7) / merged["Value"].astype(float)
    return merged.set_index("date")["gas_unit_gco2_csv"]


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


def plot_co2_grouped_bar(df):
    """Grouped bar chart: Unbatched vs Optimised CO2 per throughput level."""
    throughputs = sorted(df["throughput"].dropna().unique())

    # For each throughput, take the best (min batch CO2) configuration
    unbatched_co2 = []
    batched_co2 = []

    for t in throughputs:
        subset = df[df["throughput"] == t]
        # Use the row with the lowest batched CO2 as the "optimised" result
        best = subset.loc[subset["co2SavedKg"].idxmax()]
        unit = best["gasUnitgCO2"]
        unbatched_co2.append((best["totalIndividualGasUsed"] * unit) / 1000)
        batched_co2.append((best["totalBatchGasUsed"] * unit) / 1000)

    x = range(len(throughputs))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 6))
    bars1 = ax.bar([i - width / 2 for i in x], unbatched_co2, width, label="Unbatched Baseline CO₂", color="tab:red", alpha=0.8)
    bars2 = ax.bar([i + width / 2 for i in x], batched_co2, width, label="Optimised Batching CO₂", color="tab:green", alpha=0.8)

    ax.set_xlabel("Throughput (tx/s)")
    ax.set_ylabel("CO₂ Emissions (kg)")
    ax.set_title("Unbatched vs Optimised Batching CO₂ by Throughput")
    ax.set_xticks(list(x))
    ax.set_xticklabels([f"T={t}" for t in throughputs])
    ax.legend()
    ax.bar_label(bars1, fmt="%.3f", padding=3, fontsize=8)
    ax.bar_label(bars2, fmt="%.3f", padding=3, fontsize=8)
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()


def plot_pareto_front(df):
    """Scatter plot of Latency vs CO2 Savings to visualise the Pareto Front."""
    fig, ax = plt.subplots(figsize=(10, 6))

    throughputs = sorted(df["throughput"].dropna().unique())
    colors = plt.cm.tab10.colors

    for i, throughput in enumerate(throughputs):
        subset = df[df["throughput"] == throughput]
        x = subset["avgLatencyMs"] / 1000  # convert to seconds
        y = subset["co2SavedKg"]
        ax.scatter(x, y, label=f"T={throughput}", color=colors[i % len(colors)], s=80, zorder=3)
        for _, row in subset.iterrows():
            ax.annotate(
                f"B={int(row['batchSize'])}",
                (row["avgLatencyMs"] / 1000, row["co2SavedKg"]),
                textcoords="offset points", xytext=(6, 4), fontsize=7
            )

    ax.set_xlabel("Average Latency (s)")
    ax.set_ylabel("CO₂ Saved (kg)")
    ax.set_title("Pareto Front: Latency vs CO₂ Savings")
    ax.legend(title="Throughput")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()


def plot_pareto_front_pct(df):
    """Scatter plot of Latency vs % Carbon Saved to visualise the Pareto Front."""
    fig, ax = plt.subplots(figsize=(10, 6))

    throughputs = sorted(df["throughput"].dropna().unique())
    colors = plt.cm.tab10.colors

    for i, throughput in enumerate(throughputs):
        subset = df[df["throughput"] == throughput]
        x = subset["avgLatencyMs"] / 1000
        y = subset["percentageSaved"]
        ax.scatter(x, y, label=f"T={throughput}", color=colors[i % len(colors)], s=80, zorder=3)
        for _, row in subset.iterrows():
            ax.annotate(
                f"B={int(row['batchSize'])}",
                (row["avgLatencyMs"] / 1000, row["percentageSaved"]),
                textcoords="offset points", xytext=(6, 4), fontsize=7
            )

    ax.set_xlabel("Average Latency (s)")
    ax.set_ylabel("Carbon Emission Reduction (%)")
    ax.set_title("Pareto Front: Latency vs Carbon Emission Reduction %")
    ax.legend(title="Throughput")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()


def plot_latency_boxplot(json_files):
    """Collect all individual transaction latencies per batch size, split by throughput, and plot box plots."""
    from collections import defaultdict
    # { throughput: { batch_size: [latencies] } }
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
        ax.boxplot([data_map[throughput][s] for s in sorted_sizes], labels=sorted_sizes, patch_artist=True, showfliers=True)
        ax.set_title(f"Throughput = {throughput}")
        ax.set_xlabel("Batch Size")
        ax.grid(True, axis="y", alpha=0.3)

    axes[0].set_ylabel("Transaction Latency (s)")
    fig.suptitle("Transaction Latency Distribution by Batch Size")
    fig.tight_layout()


def plot_metric_lines_by_throughput(df, metric_column, y_label, title_prefix, scale=1.0, metric_column2=None, label1="Digiconomist", label2="CSV Model"):
    throughputs = sorted(df["throughput"].dropna().unique())

    for throughput in throughputs:
        subset = df[df["throughput"] == throughput].copy()
        intervals = sorted(subset["batchIntervalMinutes"].dropna().unique())

        for interval in intervals:
            interval_df = subset[subset["batchIntervalMinutes"] == interval].copy()
            interval_df = interval_df.sort_values("batchSize")

            fig, ax1 = plt.subplots(figsize=(10, 4))

            if metric_column2 and metric_column2 in interval_df.columns:
                v_csv  = interval_df[metric_column2] / scale
                v_digi = interval_df[metric_column] / scale

                l1, = ax1.plot(interval_df["batchSize"], v_csv, marker="o", linewidth=2, color="tab:blue", label=label2)
                ax1.set_ylabel(f"{y_label} ({label2})", color="tab:blue")
                ax1.tick_params(axis="y", labelcolor="tab:blue")
                ax1.set_yticks(sorted(v_csv.tolist()))
                ax1.yaxis.set_major_formatter(plt.FormatStrFormatter("%.2f"))

                ax2 = ax1.twinx()
                l2, = ax2.plot(interval_df["batchSize"], v_digi, marker="s", linewidth=2, color="tab:orange", label=label1)
                ax2.set_ylabel(f"{y_label} ({label1})", color="tab:orange")
                ax2.tick_params(axis="y", labelcolor="tab:orange")
                ax2.set_yticks(sorted(v_digi.tolist()))
                ax2.yaxis.set_major_formatter(plt.FormatStrFormatter("%.2f"))

                ax1.legend(handles=[l1, l2], loc="upper left")
            else:
                values = interval_df[metric_column] / scale
                avg = values.mean()
                ax1.plot(interval_df["batchSize"], values, marker="o", linewidth=2)
                ax1.axhline(avg, color="red", linestyle="--", linewidth=1.2)
                ax1.text(0.02, 0.98, f"Avg: {avg:.2f}", transform=ax1.transAxes,
                         va="top", ha="left", color="red", fontsize=9)
                ax1.set_ylabel(y_label)
                ax1.set_yticks(sorted(values.tolist()))
                ax1.yaxis.set_major_formatter(plt.FormatStrFormatter("%.2f"))

            ax1.set_title(f"{title_prefix} — Throughput={throughput}, Batch Interval={interval} min")
            ax1.set_xlabel("Batch Size")
            ax1.set_xticks(interval_df["batchSize"])
            ax1.tick_params(axis="x", rotation=45)
            ax1.grid(True, alpha=0.3)
            fig.tight_layout()

def print_summary_table(df):
    """Print a structured table of independent variables vs key numerical outputs."""
    print_header("Independent Variables vs Numerical Outputs")

    cols = {
        "Throughput": "throughput",
        "Batch Interval (min)": "batchIntervalMinutes",
        "Batch Size": "batchSize",
        "Total Gas Used": "totalBatchGasUsed",
        "Total CO2 Saved (kg)": "co2SavedKg",
        "Mean Latency (ms)": "avgLatencyMs",
        "Max Latency (ms)": "maxLatencyMs",
    }

    table = df[[v for v in cols.values() if v in df.columns]].copy()
    table = table.sort_values(["throughput", "batchIntervalMinutes", "batchSize"])
    table.columns = [k for k, v in cols.items() if v in df.columns]

    print(table.to_string(index=False))


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
    csv_gco2_series = load_csv_gas_unit_gco2()

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

            # CSV-derived model: look up the most recent date available in both CSVs
            file_date = pd.Timestamp(api_date)
            available = csv_gco2_series.index[csv_gco2_series.index <= file_date]
            if len(available) > 0:
                csv_resolved_date = available[-1]
                gas_unit_gco2_csv = float(csv_gco2_series[csv_resolved_date])
            else:
                csv_resolved_date = None
                gas_unit_gco2_csv = None

            # Fetch Digiconomist for the same date the CSV model resolved to
            digi_date = csv_resolved_date.strftime("%Y%m%d") if csv_resolved_date is not None else api_date
            if digi_date not in gco2_cache:
                gco2_cache[digi_date] = fetch_gas_unit_gco2(digi_date)
            gas_unit_gco2 = gco2_cache[digi_date]

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
                "gasUnitgCO2_csv": round(gas_unit_gco2_csv, 12) if gas_unit_gco2_csv is not None else None,
                "co2SavedKg_csv": round((gas_result["gasSaved"] * gas_unit_gco2_csv) / 1000, 4) if gas_unit_gco2_csv is not None else None,
                "co2SavedG_csv": round(gas_result["gasSaved"] * gas_unit_gco2_csv, 4) if gas_unit_gco2_csv is not None else None,
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
        "totalIndividualGasUsed", "totalBatchGasUsed", "gasSaved", "percentageSaved",
        "gasUnitgCO2", "co2SavedKg", "co2SavedG",
        "gasUnitgCO2_csv", "co2SavedKg_csv", "co2SavedG_csv",
        "avgLatencyMs", "minLatencyMs", "maxLatencyMs", "totalTransactionsAnalysed",
    ]
    df = df[[c for c in col_order if c in df.columns]]

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)

    print_header("Summary")
    print(df.to_string(index=False))
    print(f"\n✅ Results saved to: {OUTPUT_PATH}")

    print_summary_table(df)

    plot_metric_lines_by_throughput(
        df=df,
        metric_column="co2SavedKg",
        y_label="Carbon Saved (kg CO₂)",
        title_prefix="Carbon Savings vs Batch Size",
        metric_column2="co2SavedKg_csv",
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

    processed_files = [r["file"] for r in rows]
    plot_latency_boxplot([f for f in json_files if os.path.basename(f) in processed_files])

    plot_pareto_front(df)
    plot_pareto_front_pct(df)
    plot_co2_grouped_bar(df)

    plt.show()

if __name__ == "__main__":
    main()