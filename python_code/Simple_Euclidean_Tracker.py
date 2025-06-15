import pandas as pd
import numpy as np
from scipy.spatial.distance import cdist
import sys
import os

def track_with_euclidean(input_csv, output_csv, distance_threshold=30):
    """
    Perform simple object tracking using Euclidean distance between frames.

    Args:
        input_csv (str): Path to CSV containing YOLO detections.
        output_csv (str): Path to save the tracked results.
        distance_threshold (float): Maximum distance to consider match.
    """
    if not os.path.exists(input_csv):
        raise FileNotFoundError(f"Input CSV not found: {input_csv}")

    df = pd.read_csv(input_csv)
    df['x_center'] = (df['x1'] + df['x2']) / 2
    df['y_center'] = (df['y1'] + df['y2']) / 2
    df = df.sort_values(by='frame')

    tracks = []
    next_track_id = 1
    results = []

    for frame, group in df.groupby('frame'):
        detections = group[['x_center', 'y_center']].values
        assigned = [False] * len(detections)

        active_tracks = [
            t for t in tracks if not t['locked'] and (frame - t['last_seen_frame'] == 1)
        ]

        if active_tracks and len(detections) > 0:
            track_centers = np.array([t['center'] for t in active_tracks])
            dists = cdist(track_centers, detections)

            used_detections = set()
            for t_idx, track in enumerate(active_tracks):
                d_idx = np.argmin(dists[t_idx])
                if (
                    dists[t_idx][d_idx] < distance_threshold
                    and not assigned[d_idx]
                    and d_idx not in used_detections
                ):
                    x1, y1, x2, y2 = group.iloc[d_idx][['x1', 'y1', 'x2', 'y2']]
                    results.append([frame, track['id'], x1, y1, x2, y2])
                    track['center'] = detections[d_idx]
                    track['last_seen_frame'] = frame
                    track['age'] += 1
                    assigned[d_idx] = True
                    used_detections.add(d_idx)

        for idx, det in enumerate(detections):
            if not assigned[idx]:
                x1, y1, x2, y2 = group.iloc[idx][['x1', 'y1', 'x2', 'y2']]
                results.append([frame, next_track_id, x1, y1, x2, y2])
                tracks.append({
                    'id': next_track_id,
                    'center': det,
                    'last_seen_frame': frame,
                    'age': 1,
                    'locked': False
                })
                next_track_id += 1

        for trk in tracks:
            if not trk['locked'] and (frame - trk['last_seen_frame'] > 0):
                trk['locked'] = True

    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    results_df = pd.DataFrame(results, columns=['frame', 'track_id', 'x1', 'y1', 'x2', 'y2'])
    results_df.to_csv(output_csv, index=False)
    print(f" Tracking complete. Results saved to: {output_csv}")
    return output_csv

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python simple_euclidean.py <input_csv> <output_csv>")
        sys.exit(1)

    input_csv_path = sys.argv[1]
    output_csv_path = sys.argv[2]

    try:
        track_with_euclidean(input_csv_path, output_csv_path)
    except Exception as e:
        print(f" Error during tracking: {e}")
