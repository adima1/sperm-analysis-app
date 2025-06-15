import sys
import os
import subprocess
import pandas as pd  # ✅ חדש

def run_command(command, step_name=""):
    print(f"\n[INFO] Running step: {step_name}")
    print(f"[CMD] {command}\n")
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        print(f"[ERROR] Step '{step_name}' failed:\n{result.stderr}")
        raise RuntimeError(result.stderr)
    print(f"[SUCCESS] Step '{step_name}' completed.")
    print(result.stdout)

def main(video_path, output_dir):
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "python_code"))
    os.makedirs(output_dir, exist_ok=True)

    frames_dir = os.path.join(output_dir, "frames")
    yolo_output_dir = os.path.join(output_dir, "yolo_output")
    track_input_csv = os.path.join(output_dir, "sort_input.csv")
    simple_tracks_csv = os.path.join(output_dir, "simple_tracks.csv")
    final_video_path = os.path.join(output_dir, "tracked_video.mp4")
    final_summary_csv = os.path.join(output_dir, "final_summary.csv")
    graph_output = os.path.join(output_dir, "graph.png")
    model_path = os.path.join(base, "best.pt")

    # שמות הסקריפטים
    script1 = os.path.join(base, "Splits_video_into_images_and_black.py")
    script2 = os.path.join(base, "out_of_model_yolov.py")
    script3 = os.path.join(base, "from_out_model_to_csv_of_sort.py")
    script4 = os.path.join(base, "Simple_Euclidean_Tracker.py")
    script5 = os.path.join(base, "main_video_of_test_track_algoritem.py")
    script6 = os.path.join(base, "From_csv_after_correction_to_final_data.py")
    script7 = os.path.join(base, "graph_of_sperm_tracks.py")

    run_command(f"python \"{script1}\" \"{video_path}\" \"{frames_dir}\"", "Step 1 - Split video")
    run_command(f"python \"{script2}\" \"{model_path}\" \"{frames_dir}\" \"{yolo_output_dir}\" \"run\"", "Step 2 - YOLO detection")
    labels_dir = os.path.join(yolo_output_dir, "run", "labels")
    run_command(f"python \"{script3}\" \"{labels_dir}\" \"{track_input_csv}\"", "Step 3 - Convert YOLO to CSV")
    run_command(f"python \"{script4}\" \"{track_input_csv}\" \"{simple_tracks_csv}\"", "Step 4 - Euclidean tracking")
    run_command(f"python \"{script5}\" \"{frames_dir}\" \"{simple_tracks_csv}\" \"{final_video_path}\"", "Step 5 - Generate tracked video")

    # ✅ הוספת x_center ו־y_center
    try:
        df = pd.read_csv(simple_tracks_csv)
        df["x_center"] = (df["x1"] + df["x2"]) / 2
        df["y_center"] = (df["y1"] + df["y2"]) / 2
        df.to_csv(simple_tracks_csv, index=False)
    except Exception as e:
        print("⚠️ Could not add x_center/y_center:", e)

    # ✅ Summary
    video_name = os.path.basename(video_path)
    run_command(f"python \"{script6}\" \"{simple_tracks_csv}\" \"{video_name}\" \"{final_summary_csv}\"", "Step 6 - Final summary CSV")

    # ✅ Graph
    run_command(f"python \"{script7}\" \"{simple_tracks_csv}\" \"{graph_output}\"", "Step 7 - Plot graph")

    print("\n[INFO] Tracking with noise completed successfully.")
    print(f"[OUTPUT] Video: {final_video_path}")
    print(f"[OUTPUT] Labeled Frames Dir: {frames_dir}")
    print(f"[OUTPUT] Summary CSV: {final_summary_csv}")
    print(f"[OUTPUT] Graph: {graph_output}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python run_tracking_noise.py <input_video> <output_dir>")
        sys.exit(1)

    input_video = sys.argv[1]
    output_dir = sys.argv[2]
    main(input_video, output_dir)
