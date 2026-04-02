import matplotlib.pyplot as plt
import pandas as pd


def plot(
    filepath: str,
    correction: float = 0.0,
    max_time: float = 60.0,
    outlier_percentile: float = 0.01,
    window_size: int = 100,
    title: str | None = None,
) -> None:
    column_names = ["timestamp in ms", "RF power (dBm)", "RF power (mW)"]
    data = pd.read_csv(filepath, names=column_names, usecols=[0, 1, 2])

    data["RF power (dBm)"] = data["RF power (dBm)"] + correction

    # Filter to max time
    max_time_ms = max_time * 60_000
    data = data[data["timestamp in ms"] <= max_time_ms]

    print(data.head())

    data["timestamp in minutes"] = data["timestamp in ms"] / 60_000

    # Exclude lower outliers
    lower_bound_dBm = data["RF power (dBm)"].quantile(outlier_percentile)
    data = data[data["RF power (dBm)"] > lower_bound_dBm]

    lower_bound_mW = data["RF power (mW)"].quantile(outlier_percentile)
    data = data[data["RF power (mW)"] > lower_bound_mW]

    # Moving averages
    data["RF power (dBm) MA"] = data["RF power (dBm)"].rolling(window=window_size).mean()
    data["RF power (mW) MA"] = data["RF power (mW)"].rolling(window=window_size).mean()

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(5, 7))

    if title:
        fig.suptitle(title, fontsize=10)

    # Stats
    dBm_col = data["RF power (dBm)"]
    mW_col = data["RF power (mW)"]
    dBm_stats = f"min: {dBm_col.min():.3f} dBm  max: {dBm_col.max():.3f} dBm  avg: {dBm_col.mean():.3f} dBm"
    mW_stats = f"min: {mW_col.min():.2f} mW   max: {mW_col.max():.2f} mW   avg: {mW_col.mean():.2f} mW"

    ax1.plot(data["timestamp in minutes"], dBm_col, "k.", markersize=2, label="Raw Data")
    ax1.plot(data["timestamp in minutes"], data["RF power (dBm) MA"], "b-", label="Moving Average")
    ax1.set_title("RF Power (dBm)")
    ax1.set_xlabel("Timestamp (minutes)")
    ax1.set_ylabel("RF Power (dBm)")
    ax1.legend()
    ax1.grid(True, which="both", axis="y", linestyle="--", linewidth=0.5)

    ax2.plot(data["timestamp in minutes"], mW_col, "k.", markersize=2, label="Raw Data")
    ax2.plot(data["timestamp in minutes"], data["RF power (mW) MA"], "b-", label="Moving Average")
    ax2.set_title("RF Power (mW)")
    ax2.set_xlabel("Timestamp (minutes)")
    ax2.set_ylabel("RF Power (mW)")
    ax2.legend()
    ax2.grid(True, which="both", axis="y", linestyle="--", linewidth=0.5)

    fig.subplots_adjust(bottom=0.13)
    stats_text = f"dBm \u2014 {dBm_stats}\nmW  \u2014 {mW_stats}"
    fig.text(0.5, 0.02, stats_text, ha="center", fontsize=8, fontfamily="monospace")

    plt.tight_layout(rect=[0, 0.08, 1, 1])
    plt.show()
