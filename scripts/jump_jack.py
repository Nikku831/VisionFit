import cv2
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
import os

class JumpingJackCounter:
    def __init__(self, video_path):
        self.video_path = video_path
        self.cap = cv2.VideoCapture(video_path)
        
        if not self.cap.isOpened():
            raise ValueError(f"Error opening video file: {video_path}")
        
        self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        if self.fps == 0: self.fps = 30.0
        
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=50,
            varThreshold=40,
            detectShadows=False
        )
        
        self.area_history = []
        self.smoothed_areas = []
        
        self.frames = []
        self.masks = []
    
    def apply_morphology(self, mask):
        kernel = np.ones((5,5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_DILATE, kernel)
        return mask
    
    def compute_area(self, mask):
        contours, _ = cv2.findContours(
            mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )
        if not contours:
            return 0
        largest = max(contours, key=cv2.contourArea)
        return cv2.contourArea(largest)
    
    def process_video_and_save(self, output_path, skip_frames=90, prominence_factor=0.05):
        frame_idx = 0
        print(f"Processing video: {self.video_path}...")
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
            
            self.frames.append(frame.copy())
            fg_mask = self.bg_subtractor.apply(frame)
            fg_mask = self.apply_morphology(fg_mask)
            self.masks.append(fg_mask.copy())
            
            area = self.compute_area(fg_mask)
            if frame_idx >= skip_frames:
                self.area_history.append(area)
            
            frame_idx += 1
            if frame_idx % 50 == 0:
                print(f"Processed {frame_idx}/{self.total_frames}")
        
        self.cap.release()
        
        # Smooth and Count
        if self.area_history:
            self.smooth_signal()
            count, peaks = self.count_jumping_jacks(prominence_factor)
        else:
            count, peaks = 0, []

        # Save Video
        if self.frames:
            self.save_annotated_video(output_path, count, peaks, skip_frames)
        
        return count

    def smooth_signal(self, window_size=10):
        signal = np.array(self.area_history)
        if len(signal) < window_size:
            self.smoothed_areas = signal
            return
        smoothed = np.convolve(
            signal,
            np.ones(window_size)/window_size,
            mode='same'
        )
        self.smoothed_areas = smoothed
    
    def count_jumping_jacks(self, prominence_factor=0.07):
        signal = np.array(self.smoothed_areas)
        if len(signal) == 0: return 0, []
        prominence = prominence_factor * (np.max(signal) - np.min(signal))
        peaks, _ = find_peaks(
            signal,
            prominence=prominence,
            distance=15
        )
        return len(peaks), peaks
    
    def save_annotated_video(self, output_path, total_count, peaks, skip_frames):
        height, width, _ = self.frames[0].shape
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        out = cv2.VideoWriter(output_path, fourcc, self.fps, (width, height))
        
        jump_count = 0
        for i, frame in enumerate(self.frames):
            annotated = frame.copy()
            signal_index = i - skip_frames
            
            if signal_index >= 0 and signal_index < len(self.area_history):
                area = self.area_history[signal_index]
                area_ratio = area / (width * height)
                if signal_index in peaks:
                    jump_count += 1
                
                cv2.putText(annotated, f"Area: {int(area)}", (20,40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,0), 2)
                cv2.putText(annotated, f"Ratio: {area_ratio:.4f}", (20,80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,0), 2)
                cv2.putText(annotated, f"Count: {jump_count}", (20,130), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 3)
            
            mask = self.masks[i]
            small_mask = cv2.resize(mask,(200,150))
            small_mask = cv2.cvtColor(small_mask,cv2.COLOR_GRAY2BGR)
            annotated[0:150, width-200:width] = small_mask
            out.write(annotated)
        out.release()

def run_analysis(video_path, output_path):
    counter = JumpingJackCounter(video_path)
    count = counter.process_video_and_save(output_path)
    return {"jumping_jacks_count": count}

if __name__ == "__main__":
    path = input("Enter video path: ").strip('"')
    print(run_analysis(path, "output/test_jump_jack.mp4"))
