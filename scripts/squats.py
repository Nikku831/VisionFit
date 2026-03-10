import cv2
import numpy as np
import pandas as pd
import os
import json

def init_features(gray, roi):
    x, y, w0, h0 = roi
    mask = np.zeros_like(gray)
    mask[y:y+h0, x:x+w0] = 255
    return cv2.goodFeaturesToTrack(
        gray,
        maxCorners=80,
        qualityLevel=0.01,
        minDistance=5,
        mask=mask
    )

def run_analysis(video_path, output_path, roi_file_base=None):
    """
    Processes the video for Squat Analysis and saves the annotated video.
    Returns: {"squat_count": count}
    """
    if roi_file_base is None:
        roi_file_base = os.path.splitext(os.path.basename(video_path))[0]
    
    ROI_FILE = f"output/rois/rois_squats_{roi_file_base}.json"
    os.makedirs("output/rois", exist_ok=True)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    labels_tracked = ["Head", "Hip", "Palm", "Ankle"]
    cap = cv2.VideoCapture(video_path)
    ret, first_frame = cap.read()
    if not ret:
        raise ValueError(f"Could not read video: {video_path}")

    h, w = first_frame.shape[:2]
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0: fps = 30.0

    out = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))

    # ROI SELECTION
    if os.path.exists(ROI_FILE):
        with open(ROI_FILE, "r") as f:
            rois = json.load(f)
        rois = {k: tuple(v) for k, v in rois.items()}
    else:
        print("Draw ROIs in order: Head, Hip, Palm, Ankle")
        rois = {}
        for lbl in labels_tracked:
            # Note: This will open a window, which is expected behavior
            roi = cv2.selectROI(f"Select {lbl}", first_frame, showCrosshair=True)
            cv2.destroyAllWindows()
            rois[lbl] = tuple(roi)
        with open(ROI_FILE, "w") as f:
            json.dump(rois, f)

    prev_gray = cv2.cvtColor(first_frame, cv2.COLOR_BGR2GRAY)
    points = {lbl: init_features(prev_gray, rois[lbl]) for lbl in labels_tracked}

    lk_params = dict(
        winSize=(21, 21),
        maxLevel=3,
        criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01)
    )

    records = []
    frame_id = 0
    squat_count = 0
    state = "UP"
    dist_history = []
    window_size = 7
    cooldown_frames = int(fps * 0.7)
    last_count_frame = -cooldown_frames
    baseline_samples = []
    baseline_dist = None
    baseline_frames = int(fps)
    min_depth_ratio = 0.15

    while True:
        ret, frame = cap.read()
        if not ret: break

        frame_id += 1
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        centers = {}
        row = [frame_id]

        for lbl in labels_tracked:
            pts = points[lbl]
            if pts is None: continue
            next_pts, status, _ = cv2.calcOpticalFlowPyrLK(prev_gray, gray, pts, None, **lk_params)
            if next_pts is None: continue
            good_new = next_pts[status.flatten() == 1]
            if len(good_new) < 5:
                good_new = init_features(gray, rois[lbl])
                if good_new is None: continue
            pts_xy = good_new.reshape(-1, 2)
            cx = int(np.mean(pts_xy[:, 0]))
            cy = int(np.mean(pts_xy[:, 1]))
            centers[lbl] = (cx, cy)
            points[lbl] = good_new.reshape(-1, 1, 2)

        if "Head" in centers and "Hip" in centers:
            hx, hy = centers["Head"]
            tx, ty = centers["Hip"]
            centers["Neck"] = (hx, int(hy + 0.20 * (ty - hy)))

        if "Hip" in centers and "Ankle" in centers:
            hip_y = centers["Hip"][1]
            ankle_y = centers["Ankle"][1]
            vertical_dist = ankle_y - hip_y
            dist_history.append(vertical_dist)
            if len(dist_history) > window_size: dist_history.pop(0)
            smoothed_dist = np.mean(dist_history)

            if frame_id < baseline_frames:
                baseline_samples.append(smoothed_dist)
                baseline_dist = np.mean(baseline_samples)

            if baseline_dist is not None:
                compression = baseline_dist - smoothed_dist
                compression_ratio = compression / baseline_dist
                if compression_ratio > min_depth_ratio and state == "UP":
                    state = "DOWN"
                if compression_ratio < min_depth_ratio * 0.4 and state == "DOWN":
                    if frame_id - last_count_frame > cooldown_frames:
                        squat_count += 1
                        last_count_frame = frame_id
                    state = "UP"
                cv2.putText(frame, f"Compression: {compression_ratio:.2f}", (40, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                cv2.line(frame, centers["Hip"], centers["Ankle"], (0, 255, 255), 3)

        for lbl, pt in centers.items():
            cv2.circle(frame, pt, 6, (0, 255, 0), -1)
        if "Head" in centers and "Neck" in centers:
            cv2.line(frame, centers["Head"], centers["Neck"], (255, 255, 255), 2)
        if "Neck" in centers and "Hip" in centers:
            cv2.line(frame, centers["Neck"], centers["Hip"], (255, 255, 255), 2)
        if "Hip" in centers and "Ankle" in centers:
            cv2.line(frame, centers["Hip"], centers["Ankle"], (255, 255, 255), 2)
        
        cv2.putText(frame, f"Squats: {squat_count}", (40, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 4)
        
        prev_gray = gray
        out.write(frame)

    cap.release()
    out.release()
    return {"squat_count": squat_count}

if __name__ == "__main__":
    path = input("Enter video path: ").strip('"')
    print(run_analysis(path, "output/test_squats.mp4"))
