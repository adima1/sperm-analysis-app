import sys
from ultralytics import YOLO
import os

def run_yolo_inference(model_path, frames_folder, output_project, output_name):
    """
    Run YOLOv8 prediction on a folder of frames.

    Args:
        model_path (str): Path to the trained YOLO model (.pt file).
        frames_folder (str): Path to folder containing input frames.
        output_project (str): Directory for YOLO output (like 'yolo_output').
        output_name (str): Subfolder name inside the project folder.

    Returns:
        dict: Summary with success and output folder path.
    """
    if not os.path.exists(frames_folder):
        raise FileNotFoundError(f"Frames folder not found: {frames_folder}")
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")

    model = YOLO(model_path)
    results = model.predict(
        source=frames_folder,
        save_txt=True,
        save=False,
        conf=0.25,
        imgsz=256,
        project=output_project,
        name=output_name,
        exist_ok=True
    )

    output_dir = os.path.join(output_project, output_name)

    return {
        "success": True,
        "output_dir": output_dir,
        "num_images": len(results)
    }

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python predict_yolov.py <model_path> <frames_folder> <output_project> <output_name>")
        sys.exit(1)

    model_path = sys.argv[1]
    frames_folder = sys.argv[2]
    output_project = sys.argv[3]
    output_name = sys.argv[4]

    try:
        result = run_yolo_inference(model_path, frames_folder, output_project, output_name)
        print(f"YOLO prediction complete. Results in: {result['output_dir']}")
    except Exception as e:
        print(f" Error: {e}")
