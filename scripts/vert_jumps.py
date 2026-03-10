import cv2
import numpy as np
import pandas as pd
import os
import json
from scipy.signal import find_peaks, savgol_filter
from pathlib import Path

def init_features(gray, roi):
    x, y, w0, h0 = roi
    mask = np.zeros_like(gray)
    mask[y:y+h0, x:x+w0] = 255
    return cv2.goodFeaturesToTrack(gray, maxCorners=80, qualityLevel=0.01, minDistance=5, mask=mask)

def select_or_load_rois(video_name, first_frame, roi_folder):
    roi_file = f"{roi_folder}/rois_vert_{video_name}.json"
    os.makedirs(roi_folder, exist_ok=True)
    required_rois = ["Head", "Ankle"]
    rois = {}
    if os.path.exists(roi_file):
        with open(roi_file, "r") as f:
            rois = json.load(f)
        rois = {k: tuple(v) for k, v in rois.items()}
    for lbl in required_rois:
        if lbl not in rois:
            roi = cv2.selectROI(f"Select {lbl} ROI - {video_name}", first_frame, showCrosshair=True)
            cv2.destroyAllWindows()
            if roi[2] == 0: raise RuntimeError(f"{lbl} ROI selection cancelled")
            rois[lbl] = roi
    with open(roi_file, "w") as f:
        json.dump(rois, f)
    return tuple(rois["Head"]), tuple(rois["Ankle"])

def track_video(video_path, head_roi, ankle_roi):
    cap = cv2.VideoCapture(video_path)
    ret, first_frame = cap.read()
    if not ret: raise RuntimeError("Cannot read video")
    h, w = first_frame.shape[:2]
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0: fps = 30.0
    prev_gray = cv2.cvtColor(first_frame, cv2.COLOR_BGR2GRAY)
    points_head = init_features(prev_gray, head_roi)
    points_ankle = init_features(prev_gray, ankle_roi)
    lk_params = dict(winSize=(21, 21), maxLevel=3, criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01))
    records = []
    frames_for_video = []
    frame_id = 0
    while True:
        ret, frame = cap.read()
        if not ret: break
        frame_id += 1
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        nxt_h, st_h, _ = cv2.calcOpticalFlowPyrLK(prev_gray, gray, points_head, None, **lk_params)
        good_h = nxt_h[st_h.flatten() == 1] if nxt_h is not None else None
        if good_h is None or len(good_h) < 5: good_h = init_features(gray, head_roi)
        hx, hy = np.mean(good_h.reshape(-1, 2), axis=0)
        points_head = good_h.reshape(-1, 1, 2)
        nxt_a, st_a, _ = cv2.calcOpticalFlowPyrLK(prev_gray, gray, points_ankle, None, **lk_params)
        good_a = nxt_a[st_a.flatten() == 1] if nxt_a is not None else None
        if good_a is None or len(good_a) < 5: good_a = init_features(gray, ankle_roi)
        ax, ay = np.mean(good_a.reshape(-1, 2), axis=0)
        points_ankle = good_a.reshape(-1, 1, 2)
        cv2.circle(frame, (int(hx), int(hy)), 6, (0, 0, 255), -1)
        cv2.circle(frame, (int(ax), int(ay)), 6, (0, 255, 0), -1)
        cv2.line(frame, (int(hx), int(hy)), (int(ax), int(ay)), (255, 255, 255), 2)
        records.append([frame_id, hx, hy, ax, ay])
        frames_for_video.append(frame.copy())
        prev_gray = gray
    cap.release()
    df = pd.DataFrame(records, columns=["Frame", "Head_X", "Head_Y", "Ankle_X", "Ankle_Y"])
    return df, frames_for_video, fps, (w, h)

def analyze_jump(df, real_height_cm):
    ankle_y = df["Ankle_Y"].values
    head_y = df["Head_Y"].values
    body_height_px = ankle_y - head_y
    median_body_px = np.median(body_height_px)
    px_to_cm = real_height_cm / median_body_px
    if len(ankle_y) > 7:
        ankle_y_smooth = savgol_filter(ankle_y, window_length=7, polyorder=2)
    else: ankle_y_smooth = ankle_y
    peaks, _ = find_peaks(-ankle_y_smooth, prominence=5, distance=5)
    results = {'num_jumps': len(peaks), 'max_jump': 0, 'primary_jump': 0}
    if len(peaks) > 0:
        baseline_y = np.percentile(ankle_y_smooth, 80)
        jump_heights = [(baseline_y - ankle_y_smooth[p]) * px_to_cm for p in peaks]
        results['max_jump'] = max(jump_heights)
        results['primary_jump'] = jump_heights[0]
    return results

def run_analysis(video_path, output_path, real_height_cm=165):
    video_name = Path(video_path).stem
    roi_folder = "output/rois"
    cap = cv2.VideoCapture(str(video_path))
    ret, first_frame = cap.read()
    cap.release()
    if not ret: return {"status": "failed", "error": "Could not read video"}
    head_roi, ankle_roi = select_or_load_rois(video_name, first_frame, roi_folder)
    df, frames, fps, size = track_video(str(video_path), head_roi, ankle_roi)
    results = analyze_jump(df, real_height_cm)
    out = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*"mp4v"), fps, size)
    for frame in frames:
        cv2.putText(frame, f"Jumps: {results['num_jumps']}", (40, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        out.write(frame)
    out.release()
    return {"num_jumps": results['num_jumps'], "max_jump_cm": results['max_jump']}

if __name__ == "__main__":
    path = input("Enter video path: ").strip('"')
    print(run_analysis(path, "output/test_vert.mp4"))
