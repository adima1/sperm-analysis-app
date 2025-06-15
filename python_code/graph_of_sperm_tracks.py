import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np
import sys
import os

def plot_tracks(input_csv, output_image, limit=None):
    print(f"[INFO] Reading input CSV: {input_csv}")
    df = pd.read_csv(input_csv)

    if "x_center" not in df.columns or "y_center" not in df.columns:
        if {"x1", "y1", "x2", "y2"}.issubset(df.columns):
            df["x_center"] = (df["x1"] + df["x2"]) / 2
            df["y_center"] = (df["y1"] + df["y2"]) / 2
            print("[INFO] Calculated x_center and y_center from x1/x2/y1/y2")
        else:
            raise ValueError("CSV is missing required position columns.")

    required_columns = {"x_center", "y_center", "track_id", "frame"}
    if not required_columns.issubset(df.columns):
        raise ValueError("Missing required columns in CSV.")

    if df.empty:
        raise ValueError("Input CSV is empty. Cannot generate graph.")

    # 🟢 דירוג track_ids לפי אורך (כמות שורות)
    track_lengths = df.groupby("track_id").size().sort_values(ascending=False)

    # קבלת ה־N הארוכים ביותר
    if limit is not None:
        print(f"[INFO] Selecting top {limit} longest tracks")
        selected_ids = track_lengths.head(limit).index.tolist()
    else:
        selected_ids = track_lengths.index.tolist()

    # יצירת מפה לצבעים
    cmap = cm.get_cmap("hsv", len(selected_ids))
    color_map = {track_id: cmap(i) for i, track_id in enumerate(selected_ids)}

    # ציור גרף
    plt.figure(figsize=(10, 8))
    for track_id, group in df.groupby("track_id"):
        if track_id not in selected_ids:
            continue
        group_sorted = group.sort_values("frame")
        plt.plot(
            group_sorted["x_center"],
            group_sorted["y_center"],
            label=f"ID {track_id}",
        )

    plt.title("Filtered Sperm Tracks")
    plt.xlabel("x_center")
    plt.ylabel("y_center")
    plt.gca().invert_yaxis()

    plt.legend(
        loc='upper center',
        bbox_to_anchor=(0.5, -0.15),
        fontsize='small',
        title='Track IDs',
        ncol=8
    )

    plt.grid(True)
    plt.tight_layout(rect=[0, 0.15, 1, 1])

    os.makedirs(os.path.dirname(output_image), exist_ok=True)
    plt.savefig(output_image, bbox_inches='tight')
    print(f"[SUCCESS] Graph saved to: {output_image}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python graph_of_sperm_tracks.py <input_csv> <output_image_path> [limit]")
        sys.exit(1)

    input_csv = sys.argv[1]
    output_image = sys.argv[2]
    limit = int(sys.argv[3]) if len(sys.argv) >= 4 else None

    try:
        plot_tracks(input_csv, output_image, limit)
    except Exception as e:
        print(f"[ERROR] Failed to generate graph: {e}")
