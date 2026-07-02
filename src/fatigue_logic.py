import time
from collections import deque
from scipy.spatial import distance as dist

class DrowsinessMonitor:
    def __init__(self, threshold_seconds=2.0, ear_threshold=0.21, perclos_window=30, perclos_threshold=0.6):
        self.threshold_seconds = threshold_seconds
        self.ear_threshold = ear_threshold
        self.perclos_window = perclos_window
        self.perclos_threshold = perclos_threshold
        self.closed_start_time = None
        self.frame_history = deque(maxlen=self.perclos_window)
        self.perclos = 0.0

    @staticmethod
    def calculate_ear(eye_landmarks):
        """Calculate Eye Aspect Ratio (EAR) from eye landmarks."""
        A = dist.euclidean(eye_landmarks[1], eye_landmarks[5])
        B = dist.euclidean(eye_landmarks[2], eye_landmarks[4])
        C = dist.euclidean(eye_landmarks[0], eye_landmarks[3])

        if C < 1e-6:
            return 0.0

        return (A + B) / (2.0 * C)

    def update(self, left_ear, right_ear):
        avg_ear = (left_ear + right_ear) / 2.0
        closed = avg_ear < self.ear_threshold

        self.frame_history.append(closed)
        self.perclos = sum(self.frame_history) / len(self.frame_history) if self.frame_history else 0.0

        if closed:
            if self.closed_start_time is None:
                self.closed_start_time = time.time()
            elapsed = time.time() - self.closed_start_time
        else:
            self.closed_start_time = None
            elapsed = 0.0

        is_drowsy = elapsed >= self.threshold_seconds or self.perclos >= self.perclos_threshold
        return is_drowsy, avg_ear, self.perclos

    def register_no_face(self):
        self.frame_history.append(False)
        self.perclos = sum(self.frame_history) / len(self.frame_history) if self.frame_history else 0.0
        return self.perclos
