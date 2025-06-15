import cv2
import pandas as pd
import os
from natsort import natsorted
import re
import sys

def create_tracking_video(frames_dir, tracking_csv, output_video, fps=1):
    """
    Create a video and labeled images with bounding boxes and tracking IDs.
    """
    if not os.path.exists(frames_dir):
        raise FileNotFoundError(f"Frames folder not found: {frames_dir}")
    if not os.path.exists(tracking_csv):
        raise FileNotFoundError(f"Tracking CSV not found: {tracking_csv}")

    df = pd.read_csv(tracking_csv)

    frame_files = natsorted([
        f for f in os.listdir(frames_dir)
        if f.startswith('frame_') and f.endswith(('.jpg', '.png'))
    ])
    if not frame_files:
        raise ValueError("No frame images found in the directory.")

    first_frame_path = os.path.join(frames_dir, frame_files[0])
    first_frame = cv2.imread(first_frame_path)
    if first_frame is None:
        raise FileNotFoundError(f"Cannot read the first frame: {first_frame_path}")

    height, width, _ = first_frame.shape
    os.makedirs(os.path.dirname(output_video), exist_ok=True)

    # יצירת סרטון
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video, fourcc, fps, (width, height))

    # יצירת תיקיה חדשה לתמונות מתויגות
    labeled_frames_dir = os.path.join(os.path.dirname(output_video), "labeled_frames")
    os.makedirs(labeled_frames_dir, exist_ok=True)

    for filename in frame_files:
        frame_path = os.path.join(frames_dir, filename)
        frame = cv2.imread(frame_path)

        match = re.search(r'frame_(\d+)', filename)
        if not match:
            print(f" Frame number not found in filename: {filename}")
            continue

        frame_number = int(match.group(1))
        frame_tracks = df[df['frame'] == frame_number]

        for _, row in frame_tracks.iterrows():
            x1, y1, x2, y2 = map(int, [row['x1'], row['y1'], row['x2'], row['y2']])
            track_id = int(row['track_id'])
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f'ID {track_id}', (x1, y1 - 7),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # כתיבה לסרטון
        out.write(frame)

        # שמירת תמונה מתויגת
        labeled_frame_path = os.path.join(labeled_frames_dir, filename)
        cv2.imwrite(labeled_frame_path, frame)

    out.release()
    print(f" Tracking video created: {output_video}")
    print(f" Labeled frames saved to: {labeled_frames_dir}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python main_video_of_track_algoritem.py <frames_dir> <tracking_csv> <output_video>")
        sys.exit(1)

    frames_dir = sys.argv[1]
    tracking_csv = sys.argv[2]
    output_video = sys.argv[3]

    try:
        create_tracking_video(frames_dir, tracking_csv, output_video)
    except Exception as e:
        print(f"Error: {e}")
