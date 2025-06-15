import os
import csv
import sys

def convert_yolo_to_sort_csv(labels_folder, output_csv, image_width=256, image_height=256):
    """
    Convert YOLO label .txt files into a CSV formatted for SORT algorithm.

    Args:
        labels_folder (str): Folder containing YOLO .txt label files.
        output_csv (str): Path for the output CSV file.
        image_width (int): Width of the original image.
        image_height (int): Height of the original image.
    
    Returns:
        str: Path to the output CSV file.
    """
    if not os.path.exists(labels_folder):
        raise FileNotFoundError(f"Labels folder not found: {labels_folder}")

    rows = []

    for filename in sorted(os.listdir(labels_folder)):
        if not filename.endswith('.txt'):
            continue

        try:
            frame_id = int(os.path.splitext(filename)[0].split('_')[-1])
        except ValueError:
            print(f" Skipping invalid file name: {filename}")
            continue

        with open(os.path.join(labels_folder, filename), 'r') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) < 5:
                    continue

                class_id = int(parts[0])
                x_center, y_center, w, h = map(float, parts[1:5])

                x1 = (x_center - w / 2) * image_width
                y1 = (y_center - h / 2) * image_height
                x2 = (x_center + w / 2) * image_width
                y2 = (y_center + h / 2) * image_height

                confidence = 1.0  # optional confidence placeholder
                rows.append([frame_id, x1, y1, x2, y2, confidence, class_id])

    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    with open(output_csv, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['frame', 'x1', 'y1', 'x2', 'y2', 'confidence', 'class'])
        writer.writerows(rows)

    print(f" SORT CSV created: {output_csv}")
    return output_csv

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python from_out_model_to_csv_of_sort.py <labels_folder> <output_csv>")
        sys.exit(1)

    labels_folder = sys.argv[1]
    output_csv_path = sys.argv[2]

    try:
        convert_yolo_to_sort_csv(labels_folder, output_csv_path)
    except Exception as e:
        print(f" Error: {e}")
