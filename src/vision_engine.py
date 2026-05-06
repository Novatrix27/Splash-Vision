import cv2
import numpy as np
import mediapipe as mp

class VisionEngine:
    def __init__(self, camera_index=0, sensitivity=0.5, motion_threshold=2.0, mirror=True):
        self.cap = cv2.VideoCapture(camera_index)
        if not self.cap.isOpened():
            raise RuntimeError("Impossible d'ouvrir la webcam")
        self.sensitivity = sensitivity
        self.motion_threshold = motion_threshold
        self.mirror = mirror
        self.flow_scale = 0.5
        self.hand_input_size = (320, 240)

        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
        self.mp_draw = mp.solutions.drawing_utils

        ret, frame = self.cap.read()
        if not ret:
            raise RuntimeError("Impossible de lire la webcam")
        if self.mirror:
            frame = cv2.flip(frame, 1)

        small = cv2.resize(frame, (0,0), fx=self.flow_scale, fy=self.flow_scale)
        self.prev_gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        self.frame = frame
        self.cursor_pos = (frame.shape[1]//2, frame.shape[0]//2)
        self.motion_mask = None
        self.mag = None
        self.hand_landmarks = None

    def process_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return None, None, None
        if self.mirror:
            frame = cv2.flip(frame, 1)

        # MediaPipe sur image réduite
        small_frame = cv2.resize(frame, self.hand_input_size)
        small_rgb = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(small_rgb)

        self.hand_landmarks = None
        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]
            self.hand_landmarks = hand_landmarks
            h, w, _ = frame.shape
            index_tip = hand_landmarks.landmark[8]
            cx = int(index_tip.x * w)
            cy = int(index_tip.y * h)
            self.cursor_pos = (cx, cy)

        # Flux optique sur une version réduite
        small_flow = cv2.resize(frame, (0,0), fx=self.flow_scale, fy=self.flow_scale)
        small_gray = cv2.cvtColor(small_flow, cv2.COLOR_BGR2GRAY)
        flow = cv2.calcOpticalFlowFarneback(
            self.prev_gray, small_gray, None, 0.5, 3, 15, 3, 5, 1.2, 0
        )
        mag_small = np.sqrt(flow[..., 0]**2 + flow[..., 1]**2) * self.sensitivity
        self.mag = cv2.resize(mag_small, (frame.shape[1], frame.shape[0]))
        self.motion_mask = (self.mag > self.motion_threshold).astype(np.uint8)*255
        self.prev_gray = small_gray

        if not self.hand_landmarks and np.sum(self.motion_mask) > 100:
            moments = cv2.moments(self.motion_mask)
            if moments["m00"] != 0:
                cx = int(moments["m10"] / moments["m00"])
                cy = int(moments["m01"] / moments["m00"])
                self.cursor_pos = (cx, cy)

        self.frame = frame
        return frame, self.motion_mask, self.cursor_pos

    def get_motion_in_rect(self, x, y, w, h):
        if self.mag is None:
            return 0.0
        h_img, w_img = self.mag.shape
        x1, y1 = max(0,int(x)), max(0,int(y))
        x2, y2 = min(w_img,int(x+w)), min(h_img,int(y+h))
        if x2<=x1 or y2<=y1:
            return 0.0
        return float(np.mean(self.mag[y1:y2, x1:x2]))

    def release(self):
        self.cap.release()
        self.hands.close()