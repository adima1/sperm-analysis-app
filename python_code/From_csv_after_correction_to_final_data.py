import pandas as pd
import numpy as np
import os
import sys

def classify_speed(avg_velocity):
    if avg_velocity < 4:
        return "slow"
    elif avg_velocity < 12:
        return "medium"
    else:
        return "fast"

def compute_curvature_deviation(points):
    if len(points) < 3:
        return 0.0
    p0, p1 = points[0], points[-1]
    line_vec = p1 - p0
    line_len = np.linalg.norm(line_vec)
    if line_len == 0:
        return 0.0
    unit_line_vec = line_vec / line_len
    deviations = []
    for pt in points:
        vec = pt - p0
        projection_len = np.dot(vec, unit_line_vec)
        proj_point = p0 + projection_len * unit_line_vec
        deviation = np.linalg.norm(pt - proj_point)
        deviations.append(deviation)
    return round(np.mean(deviations), 2)

def extract_tracks_summary_readable(csv_path, video_name, output_path):
    df = pd.read_csv(csv_path)

    required_cols = {"frame", "track_id", "x_center", "y_center"}
    if not required_cols.issubset(df.columns):
        raise ValueError(" חסרות עמודות דרושות בקובץ הקלט")

    df = df.sort_values(by=["track_id", "frame"]).reset_index(drop=True)
    df[['dx', 'dy']] = df.groupby('track_id')[['x_center', 'y_center']].diff()
    df['velocity'] = np.sqrt(df['dx']**2 + df['dy']**2)

    output_data = []

    for track_id, group in df.groupby("track_id"):
        group_sorted = group.sort_values("frame")
        avg_velocity = group_sorted["velocity"].mean()
        max_velocity = group_sorted["velocity"].max()
        speed_category = classify_speed(avg_velocity)

        frames = group_sorted["frame"].tolist()
        velocities = group_sorted["velocity"].tolist()
        velocity_by_frames = []
        for i in range(1, len(frames)):
            v = velocities[i]
            if not pd.isna(v):
                velocity_by_frames.append((frames[i-1], frames[i], round(v, 2)))

        coords = list(zip(group_sorted["x_center"], group_sorted["y_center"]))
        coord_str = " , ".join([f"({round(x, 1)}, {round(y, 1)})" for x, y in coords])
        frames_str = ", ".join(map(str, frames))
        duration = len(set(frames))
        curvature = compute_curvature_deviation(np.array(coords))

        output_data.append({
            "track_id": track_id,
            "coordinates": coord_str,
            "duration_frames": duration,
            "frames_present": frames_str,
            "velocity_by_frames": velocity_by_frames,
            "avg_velocity": round(avg_velocity, 2),
            "max_velocity": round(max_velocity, 2),
            "speed_category": speed_category,
            "curvature_deviation": curvature,
            "video_name": video_name
        })

    # הפיכה ל־DataFrame
    output_df = pd.DataFrame(output_data)

    # טבלת ממוצעים לפי קטגוריה
    summary_rows = []
    for cat in ["slow", "medium", "fast"]:
        cat_df = output_df[output_df["speed_category"] == cat]
        if not cat_df.empty:
            summary_rows.append({
                "speed_category": f"mean_{cat}",
                "avg_velocity": round(cat_df["avg_velocity"].mean(), 2),
                "max_velocity": round(cat_df["max_velocity"].mean(), 2),
                "curvature_deviation": round(cat_df["curvature_deviation"].mean(), 2),
                "duration_frames": round(cat_df["duration_frames"].mean(), 2)
            })

    # יצירת DataFrame עם שורות הסיכום, מילוי עמודות ריקות
    summary_df = pd.DataFrame(summary_rows)
    for col in output_df.columns:
        if col not in summary_df.columns:
            summary_df[col] = ""

    # סדר עמודות אחיד ואיחוד עם הטבלה הראשית
    summary_df = summary_df[output_df.columns]
    final_df = pd.concat([output_df, summary_df], ignore_index=True)

    # שמירה לקובץ
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    final_df.to_csv(output_path, index=False)
    print(f"הקובץ הקריא נשמר:\n{output_path}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python from_csv_after_correction_to_final_data.py <input_csv> <video_name> <output_csv>")
        sys.exit(1)

    csv_path = sys.argv[1]
    video_name = sys.argv[2]
    output_path = sys.argv[3]

    try:
        extract_tracks_summary_readable(csv_path, video_name, output_path)
    except Exception as e:
        print(f"Error: {e}")
