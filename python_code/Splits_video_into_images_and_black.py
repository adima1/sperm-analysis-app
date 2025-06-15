import tifffile as tiff
import cv2
import os

def run_split_lsm_to_frames(lsm_path, output_folder):
    """
    Converts an LSM file into a sequence of normalized PNG images.

    Args:
        lsm_path (str): Path to the LSM file.
        output_folder (str): Path to the folder where the frames will be saved.

    Returns:
        dict: Summary of the process (success, number of frames, output folder)
    """
    if not os.path.exists(lsm_path):
        raise FileNotFoundError(f"LSM file not found at {lsm_path}")

    try:
        lsm_data = tiff.imread(lsm_path)
    except Exception as e:
        raise ValueError(f"Error loading LSM file: {e}")

    if len(lsm_data.shape) == 4:
        lsm_data = lsm_data.mean(axis=1)

    os.makedirs(output_folder, exist_ok=True)

    frame_count = 0
    for i, frame in enumerate(lsm_data):
        normalized_frame = cv2.normalize(frame, None, 0, 255, cv2.NORM_MINMAX).astype('uint8')
        frame_filename = os.path.join(output_folder, f"frame_{i:04d}.png")
        cv2.imwrite(frame_filename, normalized_frame)
        frame_count += 1

    return {
        "success": True,
        "frames_saved": frame_count,
        "output_folder": output_folder
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python split_lsm_to_frames.py <input_lsm_path> <output_folder>")
        sys.exit(1)

    input_lsm = sys.argv[1]
    output_dir = sys.argv[2]

    try:
        result = run_split_lsm_to_frames(input_lsm, output_dir)
        print(f"Success! {result['frames_saved']} frames saved to {result['output_folder']}")
    except Exception as e:
        print(f"Error: {e}")
