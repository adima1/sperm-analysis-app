import pandas as pd
import numpy as np
import os
import sys

# ⚙️ פרמטרים כלליים
MAX_ANGLE = 120  # זווית חדה מדי תגרום לחיתוך המסלול
MIN_FRAMES = 3   # רק מסלולים עם לפחות X פריימים ייכנסו לפלט

def cut_track_by_angle(points, group_sorted, angle_thresh=MAX_ANGLE):
    deltas = np.diff(points, axis=0)
    speeds = np.linalg.norm(deltas, axis=1)
    unit_deltas = deltas / (speeds[:, None] + 1e-6)

    for i in range(len(unit_deltas) - 1):
        dot = np.dot(unit_deltas[i], unit_deltas[i+1])
        angle_rad = np.arccos(np.clip(dot, -1.0, 1.0))
        angle_deg = np.degrees(angle_rad)
        if angle_deg > angle_thresh:
            return group_sorted.iloc[:i + 2]  # חותך עד לנקודה שלפני הזווית החריפה
    return group_sorted

def filter_tracks_by_angle(input_csv, output_csv):
    if not os.path.exists(input_csv):
        raise FileNotFoundError(f"Input file not found: {input_csv}")

    df = pd.read_csv(input_csv)

    # חישוב מרכזי תיבות
    df["x_center"] = (df["x1"] + df["x2"]) / 2
    df["y_center"] = (df["y1"] + df["y2"]) / 2

    valid_tracks = []
    for track_id, group in df.groupby("track_id"):
        group_sorted = group.sort_values("frame")
        points = group_sorted[["x_center", "y_center"]].to_numpy()

        if len(points) < MIN_FRAMES:
            continue

        partial_track = cut_track_by_angle(points, group_sorted)
        if len(partial_track) >= MIN_FRAMES:
            valid_tracks.append(partial_track)

    os.makedirs(os.path.dirname(output_csv), exist_ok=True)

    if valid_tracks:
        clean_df = pd.concat(valid_tracks)
        clean_df.to_csv(output_csv, index=False)
        print(f" Cleaned tracks saved to:\n{output_csv}")
    else:
        print(" No valid tracks found after filtering — result not saved.")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python removes_bad_sperm_tracks.py <input_csv_path> <output_csv_path>")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]

    filter_tracks_by_angle(input_path, output_path)
