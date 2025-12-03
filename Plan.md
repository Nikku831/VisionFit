# Project Title: "VisionFit": Automated Athletic Talent Identification System using Computer Vision

**Domain:** Computer Vision / Sports Analytics

**Target Application:** Sports Authority of India (SAI) / Remote Talent Scouting

---

## 1. Problem Statement & Motivation
* **The Challenge:** Identifying athletic talent in rural India is hindered by a lack of infrastructure and standardized assessment facilities. Current methods rely on manual observation, which is subjective, prone to human error, and logistically difficult to scale.
* **The Need:** A low-cost, smartphone-based solution that allows aspiring athletes to perform standard fitness tests (Sit-ups, Shuttle Run, Vertical Jump) and receive immediate, verified scoring without human intervention.
* **Societal Impact:** Democratizing access to government sports schemes (Khelo India) by enabling "at-home" preliminary trials.

---

## 2. Literature Survey & Scientific Validation
To ensure the technical and scientific viability of this project, we referenced the following core studies:

### 2.1 Technical Feasibility (Pose Estimation)
* **Reference:** *S. Sharma et al., "AI Human Fitness Tracker using Computer Vision with MediaPipe," IJRASET, 2024.*
* **Relevance:** This study validates the use of **MediaPipe’s lightweight 33-landmark topology** for real-time exercise correction. It demonstrates that geometric heuristic methods (calculating vector angles between joints) achieve >95% accuracy for repetition counting on CPU-based devices (standard smartphones), eliminating the need for heavy GPUs.

### 2.2 Scientific Validation (Vertical Jump Physics)
* **Reference:** *C. Balsalobre-Fernández et al., "Validity and reliability of smartphone applications for measuring vertical jump," Journal of Sports Sciences, 2015 (Revalidated 2023).*
* **Relevance:** This paper compares the **"Flight Time Method"** (calculating height via time in air: $h = 1/2gt^2$) against laboratory Force Plates (the gold standard).
* **Key Finding:** The smartphone video method showed a **correlation of r = 0.97** with force plates, proving that our proposed "Flight Time" logic is scientifically valid for power assessment.

### 2.3 Domain Context (Sit-up Assessment)
* **Reference:** *Y. Zhang, "Research on sit-up counting method based on human skeleton key point detection," 2024.*
* **Relevance:** Defines the specific biomechanical thresholds for a valid sit-up:
    1.  **Hip Angle > 150°** (Supine position).
    2.  **Hip Angle < 60°** (Flexion position).
    This establishes the "Ground Truth" for our algorithm's state machine.

---

## 3. Proposed Solution
We propose a mobile-compatible Computer Vision pipeline that utilizes **Pose Estimation** to analyze video feeds of athletes performing specific test batteries. The system acts as an "AI Referee," counting repetitions, measuring timing, and detecting foul play (cheating) in real-time.

---

## 4. Scope of Work (The 3 Selected Tests)
We have selected three core tests that cover the fundamental pillars of physical fitness: **Muscular Endurance**, **Agility**, and **Explosive Power**.

### Test A: Sit-Ups (Muscular Endurance)
* **Objective:** Count valid repetitions in 1 minute.
* **Metric:** Count (Integer).
* **Key Challenge:** Distinguishing between a "partial rep" and a "full rep."
* **Logic:** Tracking the angle between the **Shoulder**, **Hip**, and **Knee**.
* **Pass Criteria:**
    * *State 1 (Down):* Hip Angle $> 150^\circ$ (Shoulders touching ground).
    * *State 2 (Up):* Hip Angle $< 60^\circ$ (Elbows near knees).

### Test B: Vertical Jump (Explosive Power)
* **Objective:** Measure the height of a jump to assess leg power.
* **Metric:** Height (Centimeters).
* **Key Challenge:** Measuring distance without a reference object in the frame.
* **Logic (Flight Time Method):** We utilize the physics of projectile motion by calculating the time difference ($\Delta t$) between the moment of take-off (toes leave ground) and landing (toes touch ground).
* **Formula:**
    $$Height = \frac{1}{2} \cdot g \cdot (\frac{\Delta t}{2})^2$$
    *(Where $g = 9.8 m/s^2$)*

### Test C: Shuttle Run (Agility)
* **Objective:** Measure time taken to run between two points (10m apart).
* **Metric:** Time (Seconds).
* **Key Challenge:** Tracking the user as they move far away from the camera.
* **Logic (ROI Crossing):**
    * Define "Line A" and "Line B" in the video frame.
    * Track the **Center of Mass (Hip Keypoint)**.
    * Detect event when the coordinate $X_{hip}$ crosses the threshold of Line A or Line B.
    * Measure time elapsed between crossings.

---

## 5. Technical Methodology (Pipeline)

The system follows a 4-stage pipeline:

1.  **Input Acquisition:** Video stream (Webcam/Smartphone Camera). Resolution optimized to 640x480 for speed.
2.  **Pose Estimation (The Core):**
    * **Model:** **MediaPipe Pose** (Google).
    * **Why?** It is lightweight, runs on CPU (making it feasible for mobile phones), and provides 33 3D-landmarks ($x, y, z$).
3.  **Geometric Analysis:**
    * Extract coordinates of relevant joints (e.g., Ankle, Knee, Hip, Shoulder).
    * Apply trigonometric calculations (Euclidean distance, Arctan2 for angles).
4.  **State Machine & Heuristics:**
    * Classify movements into states (e.g., "Jumping", "Standing", "Turning").
    * Apply "Anti-Cheat" thresholds (e.g., if a jump flight time is $> 0.8s$ but height change is minimal, flag as anomaly).

---

## 6. Expected Deliverables (For End of Semester)
1.  A functional Python prototype capable of processing a video file.
2.  Real-time overlay showing Rep Count and Form Correction (e.g., "Go Lower").
3.  A CSV/JSON report generation of the athlete's performance.
