import sys
import os
import subprocess

def run_command(command):
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        print("Error:", result.stderr)
        raise RuntimeError(result.stderr)
    print("Output:", result.stdout)

def main(video_path, output_dir):
    base = os.path.dirname(os.path.abspath(__file__))  # server/
    python_dir = os.path.join(base, "..", "python_code")  # ../python_code

    os.makedirs(output_dir, exist_ok=True)

    frames_dir = os.path.join(output_dir, "frames")
    yolo_output = os.path.join(output_dir, "yolo_output")
    final_video = os.path.join(output_dir, "labeled_video.mp4")
    model_path = os.path.join(python_dir, "best.pt")

    # 1. פיצול
    script1 = os.path.join(python_dir, "Splits_video_into_images_and_black.py")
    run_command(f"python \"{script1}\" \"{video_path}\" \"{frames_dir}\"")

    # 2. זיהוי
    script2 = os.path.join(python_dir, "out_of_model_yolov.py")
    run_command(f"python \"{script2}\" \"{model_path}\" \"{frames_dir}\" \"{yolo_output}\" \"run\"")

    # 3. וידאו
    labels_dir = os.path.join(yolo_output, "run", "labels")
    script3 = os.path.join(python_dir, "video_of_test_out_yolov.py")
    run_command(f"python \"{script3}\" \"{frames_dir}\" \"{labels_dir}\" \"{final_video}\"")

    print(f"\n Detection completed. Output video:\n{final_video}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python run_detection_only.py <input_video> <output_dir>")
        sys.exit(1)

    input_video = sys.argv[1]
    output_dir = sys.argv[2]
    main(input_video, output_dir)
