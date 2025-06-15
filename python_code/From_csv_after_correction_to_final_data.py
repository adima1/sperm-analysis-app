import pandas as pd
import os
import sys

def extract_tracks_summary_readable(csv_path, video_name, output_path):
    # טען את הקובץ
    df = pd.read_csv(csv_path)

    # ודא שיש את העמודות הדרושות
    required_cols = {"frame", "track_id", "x_center", "y_center"}
    if not required_cols.issubset(df.columns):
        raise ValueError(" חסרות עמודות דרושות בקובץ הקלט")

    # רשימת נתונים למסלול
    output_data = []

    # קיבוץ לפי track_id
    for track_id, group in df.groupby("track_id"):
        group_sorted = group.sort_values("frame")
        coords = list(zip(group_sorted["x_center"], group_sorted["y_center"]))
        coord_str = " , ".join([f"({round(x, 1)}, {round(y, 1)})" for x, y in coords])
        duration = group_sorted["frame"].nunique()
        frames = group_sorted["frame"].tolist()
        frames_str = ", ".join(map(str, frames))  # הפוך לרשימה מופרדת בפסיקים

        output_data.append({
            "track_id": track_id,
            "coordinates": coord_str,
            "duration_frames": duration,
            "frames_present": frames_str,  # ✅ עמודה חדשה
            "video_name": video_name
        })

    # יצירת טבלה חדשה
    output_df = pd.DataFrame(output_data)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    output_df.to_csv(output_path, index=False)
    print(f" הקובץ הקריא נשמר:\n{output_path}")

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
        print(f" Error: {e}")
