#!/usr/bin/env python3
"""Generate visualizations from a candump -L log."""
import argparse
import os

import matplotlib
matplotlib.use("Agg")  # no display needed, just save files
import matplotlib.pyplot as plt

from analyze_can import load_log, per_id_stats


def plot_frequency(df, stats, outdir):
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(stats["id"], stats["frames"], color="#4C72B0")
    ax.set_ylabel("Frame count")
    ax.set_title("Frames per CAN ID")
    fig.tight_layout()
    fig.savefig(os.path.join(outdir, "frequency.png"), dpi=150)
    plt.close(fig)


def plot_timeline(df, outdir):
    fig, ax = plt.subplots(figsize=(10, 4))
    ids = sorted(df["can_id"].unique())
    for i, can_id in enumerate(ids):
        g = df[df["can_id"] == can_id]
        ax.scatter(g["time"], [i] * len(g), s=2, label=f"0x{can_id:03X}")
    ax.set_yticks(range(len(ids)))
    ax.set_yticklabels([f"0x{c:03X}" for c in ids])
    ax.set_xlabel("Time (s)")
    ax.set_title("Message timeline")
    fig.tight_layout()
    fig.savefig(os.path.join(outdir, "timeline.png"), dpi=150)
    plt.close(fig)


def plot_period_jitter(df, outdir):
    ids = sorted(df["can_id"].unique())
    fig, axes = plt.subplots(len(ids), 1, figsize=(8, 2 * len(ids)), sharex=False)
    for ax, can_id in zip(axes, ids):
        g = df[df["can_id"] == can_id]
        dt_ms = g["time"].diff().dropna() * 1000
        ax.plot(dt_ms.values, lw=0.7)
        ax.set_ylabel(f"0x{can_id:03X}\nΔt (ms)", fontsize=8)
    axes[-1].set_xlabel("Frame index")
    fig.suptitle("Inter-frame period per ID (spikes = gaps/anomalies)")
    fig.tight_layout()
    fig.savefig(os.path.join(outdir, "period_jitter.png"), dpi=150)
    plt.close(fig)


def plot_payload_byte(df, can_id, byte_index, outdir):
    g = df[df["can_id"] == can_id]
    values = g["data"].apply(lambda d: int(d[byte_index * 2: byte_index * 2 + 2], 16))
    fig, ax = plt.subplots(figsize=(8, 3))
    ax.plot(g["time"], values, lw=0.8)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel(f"Byte {byte_index} value")
    ax.set_title(f"0x{can_id:03X} — payload byte {byte_index} over time")
    fig.tight_layout()
    fname = f"payload_0x{can_id:03X}_byte{byte_index}.png"
    fig.savefig(os.path.join(outdir, fname), dpi=150)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("logfile")
    ap.add_argument("--outdir", default="docs/plots")
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    df = load_log(args.logfile)
    stats = per_id_stats(df)

    plot_frequency(df, stats, args.outdir)
    plot_timeline(df, args.outdir)
    plot_period_jitter(df, args.outdir)

    # Plot the first varying byte for each ID that actually varies
    for _, row in stats.iterrows():
        if row["varying_bytes"] != "-":
            can_id = int(row["id"], 16)
            byte_idx = int(row["varying_bytes"].split(",")[0])
            plot_payload_byte(df, can_id, byte_idx, args.outdir)

    print(f"Saved plots to {args.outdir}/")


if __name__ == "__main__":
    main()
