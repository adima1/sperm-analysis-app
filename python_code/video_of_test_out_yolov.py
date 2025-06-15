import os
import sys
import cv2
from glob import glob

def create_video_with_boxes(images_dir, labels_dir, output_video_path, image_width=256, image_height=256):
    """
    Create a video from images and YOLO label files,
    and save labeled frames as individual images (bounding boxes only, no text).
    """
    image_files = sorted(glob(os.path.join(images_dir, "*.png")))
    if not image_files:
        raise FileNotFoundError("No images found in the directory.")

    sample_img = cv2.imread(image_files[0])
    if sample_img is None:
        raise ValueError("Sample image could not be loaded.")

    h, w, _ = sample_img.shape
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video_writer = cv2.VideoWriter(output_video_path, fourcc, 10, (w, h))

    # Create folder to store labeled frames
    labeled_frames_dir = os.path.join(os.path.dirname(output_video_path), "labeled_frames")
    os.makedirs(labeled_frames_dir, exist_ok=True)

    for img_path in image_files:
        img_name = os.path.basename(img_path)
        label_name = os.path.splitext(img_name)[0] + '.txt'
        label_path = os.path.join(labels_dir, label_name)

        frame = cv2.imread(img_path)
        if frame is None:
            continue

        if os.path.exists(label_path):
            with open(label_path, 'r') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 5:
                        cls_id, xc, yc, bw, bh = map(float, parts[:5])
                        x1 = int((xc - bw / 2) * w)
                        y1 = int((yc - bh / 2) * h)
                        x2 = int((xc + bw / 2) * w)
                        y2 = int((yc + bh / 2) * h)
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        # Write frame to video
        video_writer.write(frame)

        # Save labeled frame as image
        labeled_frame_path = os.path.join(labeled_frames_dir, img_name)
        cv2.imwrite(labeled_frame_path, frame)

    video_writer.release()
    return {
        "success": True,
        "output_video": output_video_path,
        "labeled_frames_dir": labeled_frames_dir,
        "num_frames": len(image_files)
    }

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python video_of_test_out_yolov.py <images_dir> <labels_dir> <output_video_path>")
        sys.exit(1)

    images_dir = sys.argv[1]
    labels_dir = sys.argv[2]
    output_video_path = sys.argv[3]

    try:
        result = create_video_with_boxes(images_dir, labels_dir, output_video_path)
        print(f"Video created successfully: {result['output_video']}")
        print(f"Labeled frames saved to: {result['labeled_frames_dir']}")
    except Exception as e:
        print(f"Error: {e}")
