# Project Title: **"VisionFit"**
**Automated Athletic Talent Identification System using Computer Vision**

**Domain:** Computer Vision / Sports Analytics  
**Target Application:** Sports Authority of India (SAI) / Remote Talent Scouting  

---

## 1. Problem Statement & Motivation
* **The Challenge:** Identifying athletic talent in rural India is hindered by the lack of standardized assessment facilities and trained evaluators. Current fitness tests such as balance, coordination, and muscular endurance are manually supervised, making them subjective and difficult to scale.
* **The Need:** A low-cost, smartphone-based solution that allows aspiring athletes to perform **standard physical fitness tests** (Plate Tapping, Flamingo Balance, Alternate Hand Wall Toss, Squats) at home and receive **objective, verified scoring** without human intervention.
* **Societal Impact:** Democratizing access to government sports schemes (e.g., *Khelo India*) by enabling **remote, AI-verified preliminary trials**.

---

## 2. Literature Survey & Scientific Validation

### 2.1 Technical Feasibility (Pose Estimation)
* **Reference:** *S. Sharma et al., "AI Human Fitness Tracker using Computer Vision with MediaPipe," IJRASET, 2024.*
* **Relevance:** Validates **MediaPipe Pose (33 landmarks)** for real-time human movement analysis on CPU-based devices. The study shows that **joint-angle heuristics and temporal thresholds** are sufficient for accurately evaluating repetitive and coordination-based exercises.

### 2.2 Scientific Validation (Balance & Coordination Tests)
* **Reference:** *Eurofit Test Battery Manual, Council of Europe.*
* **Relevance:** Plate Tapping, Flamingo Balance, and Wall Toss are internationally standardized tests for **speed of limb movement, balance, and hand–eye coordination**, making them ideal candidates for automation using vision-based temporal and spatial measurements.

### 2.3 Biomechanical Validation (Squat Assessment)
* **Reference:** *McKean et al., “Biomechanics of the squat exercise,” Journal of Strength and Conditioning Research.*
* **Relevance:** Defines valid squat depth using **hip–knee–ankle alignment**, supporting the use of **joint angle thresholds** to distinguish partial vs. full squats.

---

## 3. Proposed Solution
We propose a **mobile-compatible Computer Vision system** that acts as an **AI Referee**, automatically evaluating standardized physical fitness tests using **pose estimation, geometric reasoning, and state machines**. The system ensures **objectivity, repeatability, and scalability** in athletic screening.

---

## 4. Scope of Work (Selected Test Battery)
The selected tests cover **speed, balance, coordination, and muscular endurance**, which are critical indicators in early-stage athletic talent identification.

---

### Test A: Plate Tapping Test (Speed & Coordination)
* **Objective:** Measure upper-limb movement speed.
* **Metric:** Time (Seconds) for 25 cycles.
* **Key Challenge:** Accurate detection of alternating hand taps.
* **Logic:**
  * Track **Left Wrist** and **Right Wrist** keypoints.
  * Define two virtual tap zones on the left and right.
  * Count a valid cycle when hands alternate and cross the respective zones.
* **Anti-Cheat:** Invalid if the same hand taps consecutively.

---

### Test B: Flamingo Balance Test (Static Balance)
* **Objective:** Measure balance by counting loss-of-balance attempts in 1 minute.
* **Metric:** Number of balance losses (Lower is better).
* **Key Challenge:** Detecting instability and foot contact.
* **Logic:**
  * Track **Ankle, Knee, Hip, and Center of Mass**.
  * Monitor horizontal sway and foot-ground contact.
  * A trial is marked invalid when the raised foot touches the ground or excessive COM displacement is detected.

---

### Test C: Alternate Hand Wall Toss Test (Hand–Eye Coordination)
* **Objective:** Count successful catches in 30 seconds.
* **Metric:** Number of successful catches.
* **Key Challenge:** Detecting throw–catch cycles without a physical sensor.
* **Logic:**
  * Track **Wrist trajectory** and sudden velocity reversals.
  * Detect throw when the hand moves rapidly away from the wall.
  * Detect catch when the hand decelerates sharply near the torso.
* **Anti-Cheat:** Invalid if the same hand performs consecutive catches.

---

### Test D: Squats (Muscular Endurance & Lower-Body Strength)
* **Objective:** Count valid squats in 1 minute.
* **Metric:** Repetition Count.
* **Key Challenge:** Distinguishing partial squats from full squats.
* **Logic:**
  * Track **Hip, Knee, and Ankle** joints.
  * Compute knee and hip angles.
* **Pass Criteria:**
  * **Down State:** Knee angle < 70°, Hip below knee level.
  * **Up State:** Knee angle > 160°, Full extension.
* **Anti-Cheat:** Reject rapid oscillations without full extension.

---

## 5. Technical Methodology (Pipeline)

1. **Input Acquisition:** Smartphone/Webcam video stream (optimized to 640×480).
2. **Pose Estimation:**
   * **Model:** MediaPipe Pose (Google).
   * **Why:** Lightweight, CPU-based, real-time inference.
3. **Geometric Analysis:**
   * Joint angles, distances, velocity, and center-of-mass tracking.
4. **State Machine & Heuristics:**
   * Movement state classification (e.g., *Balanced / Unbalanced*, *Down / Up*).
   * Rule-based anomaly detection for cheating or invalid form.

---

## 6. Expected Deliverables
1. A functional Python prototype capable of processing video input.
2. Real-time visual overlays (timer, repetition count, form warnings).
3. Automated CSV/JSON performance reports for each athlete.
