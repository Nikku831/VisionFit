# flamingo_balance_modular.py
# VisionFit – Flamingo Balance Test 

import cv2
import numpy as np
import os

# ---------------- PARAMETERS ----------------
STABLE_SHIFT_THR = 12.0       # stable balance
UNSTABLE_SHIFT_THR = 25.0     # clear instability
SMOOTH_ALPHA = 0.8
MIN_CONTOUR_AREA = 2000
# --------------------------------------------

def run_analysis(video_path, output_path):
    """
    Processes the video for Flamingo Balance Test and saves the annotated video.
    Returns: (balance_time, stability_score, instability_events)
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video file: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0: fps = 30.0

    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    writer = cv2.VideoWriter(
        output_path,
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps, (w, h)
    )

    fgbg = cv2.createBackgroundSubtractorMOG2()

    prev_centroid = None
    prev_shift = 0.0

    stable_frames = 0
    instability_events = 0
    total_frames = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        fgmask = fgbg.apply(frame)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        clean = cv2.morphologyEx(fgmask, cv2.MORPH_OPEN, kernel)
        clean = cv2.morphologyEx(clean, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(
            clean, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        contours = [c for c in contours if cv2.contourArea(c) > MIN_CONTOUR_AREA]

        status = "N/A"
        color = (127, 127, 127)

        if contours:
            cnt = max(contours, key=cv2.contourArea)
            M = cv2.moments(cnt)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])

                if prev_centroid is None:
                    shift = 0.0
                else:
                    shift = np.linalg.norm(
                        np.array([cx, cy]) - np.array(prev_centroid)
                    )

                shift = SMOOTH_ALPHA * prev_shift + (1 - SMOOTH_ALPHA) * shift

                # -------- FRAME-WISE STABILITY --------
                if shift < STABLE_SHIFT_THR:
                    stable_frames += 1
                    status = "STABLE"
                    color = (0, 255, 0)
                else:
                    status = "UNSTABLE"
                    color = (0, 0, 255)

                if shift > UNSTABLE_SHIFT_THR:
                    instability_events += 1
                # -------------------------------------

                cv2.drawContours(frame, [cnt], -1, (255, 0, 0), 2)
                cv2.circle(frame, (cx, cy), 5, (0, 255, 255), -1)
                
                prev_centroid = (cx, cy)
                prev_shift = shift

        total_frames += 1
        cv2.putText(
            frame, status, (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2
        )

        writer.write(frame)

    cap.release()
    writer.release()

    balance_time = stable_frames / fps
    stability_score = stable_frames / total_frames if total_frames > 0 else 0.0

    return {
        "balance_time_sec": balance_time,
        "stability_score": stability_score,
        "instability_events": instability_events
    }

if __name__ == "__main__":
    # Test execution
    input_path = input("Enter video path: ").strip('"')
    output_path = "output/test_flam_bal.mp4"
    results = run_analysis(input_path, output_path)
    print(results)
