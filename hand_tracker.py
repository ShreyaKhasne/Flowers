import cv2
import numpy as np
import math
import time
import os
import urllib.request

class HandTracker:
    def __init__(self, max_hands=2, detection_confidence=0.6, tracking_confidence=0.6):
        self.max_hands = max_hands
        self.smoothing_alpha = 0.4
        self.smoothed_landmarks = {}
        self.last_positions = {}
        self.last_time = time.time()
        
        self.cap = None
        self.camera_active = False
        self.use_tasks_api = False
        self.detector = None
        self.mp_hands = None

        self._init_mediapipe()

    def _init_mediapipe(self):
        """Tries initializing MediaPipe Tasks API (1.0+), or legacy mp.solutions, or fallback."""
        try:
            from mediapipe.tasks import python
            from mediapipe.tasks.python import vision
            import mediapipe as mp

            model_path = os.path.join(os.path.dirname(__file__), "hand_landmarker.task")
            if not os.path.exists(model_path):
                print("[HandTracker] Downloading MediaPipe hand_landmarker.task model...")
                url = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
                urllib.request.urlretrieve(url, model_path)
                print("[HandTracker] Downloaded hand_landmarker.task successfully!")

            base_options = python.BaseOptions(model_asset_path=model_path)
            options = vision.HandLandmarkerOptions(
                base_options=base_options,
                num_hands=self.max_hands,
                min_hand_detection_confidence=0.5,
                min_hand_presence_confidence=0.5
            )
            self.detector = vision.HandLandmarker.create_from_options(options)
            self.mp_module = mp
            self.use_tasks_api = True
            print("[HandTracker] Initialized MediaPipe Tasks HandLandmarker Engine.")
            return
        except Exception as e1:
            print(f"[HandTracker] MediaPipe Tasks API setup failed: {e1}")

        try:
            import mediapipe as mp
            if hasattr(mp, "solutions") and hasattr(mp.solutions, "hands"):
                self.mp_hands = mp.solutions.hands.Hands(
                    static_image_mode=False,
                    max_num_hands=self.max_hands,
                    min_detection_confidence=0.6,
                    min_tracking_confidence=0.6
                )
                self.use_tasks_api = False
                print("[HandTracker] Initialized Legacy MediaPipe Solutions Engine.")
                return
        except Exception as e2:
            print(f"[HandTracker] Legacy MediaPipe Solutions setup failed: {e2}")

        print("[HandTracker] Running in OpenCV + Mouse fallback mode.")

    def init_camera(self, camera_index=0):
        if self.cap is not None:
            self.cap.release()

        self.cap = cv2.VideoCapture(camera_index)
        if not self.cap.isOpened():
            self.cap = cv2.VideoCapture(1)

        if self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            self.camera_active = True
            print("[HandTracker] Webcam initialized successfully!")
            return True
        else:
            self.camera_active = False
            print("[HandTracker] Webcam unavailable. Using interactive mouse mode.")
            return False

    def process_frame(self, target_width, target_height):
        current_time = time.time()
        dt = max(0.001, current_time - self.last_time)
        self.last_time = current_time

        if not self.camera_active or self.cap is None:
            return None, []

        ret, frame = self.cap.read()
        if not ret or frame is None:
            return None, []

        frame = cv2.flip(frame, 1)
        hand_data_list = []

        if self.use_tasks_api and self.detector is not None:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = self.mp_module.Image(image_format=self.mp_module.ImageFormat.SRGB, data=rgb_frame)
            detection_result = self.detector.detect(mp_image)

            if detection_result.hand_landmarks:
                for hand_idx, hand_landmarks in enumerate(detection_result.hand_landmarks):
                    handedness = "Right"
                    if detection_result.handedness and hand_idx < len(detection_result.handedness):
                        handedness = detection_result.handedness[hand_idx][0].category_name

                    raw_pts = []
                    for lm in hand_landmarks:
                        px = int(lm.x * target_width)
                        py = int(lm.y * target_height)
                        raw_pts.append((px, py, lm.z))

                    hand_info = self._format_hand_info(hand_idx, handedness, raw_pts, target_width, target_height, dt)
                    hand_data_list.append(hand_info)

        elif self.mp_hands is not None:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.mp_hands.process(rgb_frame)
            if results.multi_hand_landmarks:
                for hand_idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
                    handedness = "Right"
                    if results.multi_handedness and hand_idx < len(results.multi_handedness):
                        handedness = results.multi_handedness[hand_idx].classification[0].label

                    raw_pts = []
                    for lm in hand_landmarks.landmark:
                        px = int(lm.x * target_width)
                        py = int(lm.y * target_height)
                        raw_pts.append((px, py, lm.z))

                    hand_info = self._format_hand_info(hand_idx, handedness, raw_pts, target_width, target_height, dt)
                    hand_data_list.append(hand_info)

        return frame, hand_data_list

    def _format_hand_info(self, hand_idx, handedness, raw_pts, target_width, target_height, dt):
        """Applies EMA smoothing and extracts gesture landmarks including extended finger count."""
        if hand_idx not in self.smoothed_landmarks:
            smoothed_pts = raw_pts
        else:
            prev_pts = self.smoothed_landmarks[hand_idx]
            smoothed_pts = []
            for i in range(len(raw_pts)):
                sx = self.smoothing_alpha * raw_pts[i][0] + (1 - self.smoothing_alpha) * prev_pts[i][0]
                sy = self.smoothing_alpha * raw_pts[i][1] + (1 - self.smoothing_alpha) * prev_pts[i][1]
                sz = self.smoothing_alpha * raw_pts[i][2] + (1 - self.smoothing_alpha) * prev_pts[i][2]
                smoothed_pts.append((int(sx), int(sy), sz))

        self.smoothed_landmarks[hand_idx] = smoothed_pts

        wrist = (smoothed_pts[0][0], smoothed_pts[0][1])
        thumb_tip = (smoothed_pts[4][0], smoothed_pts[4][1])
        index_tip = (smoothed_pts[8][0], smoothed_pts[8][1])
        middle_tip = (smoothed_pts[12][0], smoothed_pts[12][1])
        ring_tip = (smoothed_pts[16][0], smoothed_pts[16][1])
        pinky_tip = (smoothed_pts[20][0], smoothed_pts[20][1])

        mcp_5 = (smoothed_pts[5][0], smoothed_pts[5][1])
        mcp_9 = (smoothed_pts[9][0], smoothed_pts[9][1])
        mcp_17 = (smoothed_pts[17][0], smoothed_pts[17][1])
        palm_center = (
            int((wrist[0] + mcp_5[0] + mcp_9[0] + mcp_17[0]) / 4),
            int((wrist[1] + mcp_5[1] + mcp_9[1] + mcp_17[1]) / 4)
        )

        hand_scale = math.hypot(mcp_9[0] - wrist[0], mcp_9[1] - wrist[1])
        hand_scale = max(1.0, hand_scale)

        # Extended Fingers Counting (for gesture theme switching: 1 to 5 fingers!)
        extended_count = 0
        
        # Index (8 tip vs 6 pip)
        if smoothed_pts[8][1] < smoothed_pts[6][1]:
            extended_count += 1
        # Middle (12 tip vs 10 pip)
        if smoothed_pts[12][1] < smoothed_pts[10][1]:
            extended_count += 1
        # Ring (16 tip vs 14 pip)
        if smoothed_pts[16][1] < smoothed_pts[14][1]:
            extended_count += 1
        # Pinky (20 tip vs 18 pip)
        if smoothed_pts[20][1] < smoothed_pts[18][1]:
            extended_count += 1
        # Thumb (4 tip vs 2 mcp X distance depending on handedness)
        if handedness == "Right":
            if smoothed_pts[4][0] < smoothed_pts[2][0]:
                extended_count += 1
        else:
            if smoothed_pts[4][0] > smoothed_pts[2][0]:
                extended_count += 1

        # Pinch Detection
        pinch_dist = math.hypot(index_tip[0] - thumb_tip[0], index_tip[1] - thumb_tip[1])
        norm_pinch = pinch_dist / hand_scale
        is_pinching = norm_pinch < 0.38
        pinch_pos = (
            int((index_tip[0] + thumb_tip[0]) / 2),
            int((index_tip[1] + thumb_tip[1]) / 2)
        )

        # Open Palm Detection
        is_open_palm = extended_count >= 4

        # Velocity Vector
        last_pos = self.last_positions.get(hand_idx, index_tip)
        vx = (index_tip[0] - last_pos[0]) / dt
        vy = (index_tip[1] - last_pos[1]) / dt
        speed = math.hypot(vx, vy)
        self.last_positions[hand_idx] = index_tip

        return {
            "hand_idx": hand_idx,
            "label": handedness,
            "landmarks": smoothed_pts,
            "wrist": wrist,
            "palm_center": palm_center,
            "fingertips": [thumb_tip, index_tip, middle_tip, ring_tip, pinky_tip],
            "index_tip": index_tip,
            "thumb_tip": thumb_tip,
            "is_pinching": is_pinching,
            "pinch_pos": pinch_pos,
            "pinch_norm": norm_pinch,
            "is_open_palm": is_open_palm,
            "finger_count": extended_count,
            "velocity": (vx, vy),
            "speed": speed,
            "hand_scale": hand_scale
        }

    def release(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        if self.mp_hands is not None:
            self.mp_hands.close()
