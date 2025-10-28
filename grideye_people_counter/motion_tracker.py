# motion_tracker.py
import numpy as np
from collections import deque
from config import ENTRY_LINE_X, DIRECTION_SMOOTH, FRAME_BUFFER_SIZE

class MotionTracker:
    def __init__(self):
        self.buffer = deque(maxlen=FRAME_BUFFER_SIZE)
        self.people_inside = 0
        self.entry_events = []
        self.exit_events = []

    def update(self, blobs):
        self.buffer.append(blobs)
        if len(self.buffer) < 2:
            return self.people_inside

        prev, curr = self.buffer[-2], self.buffer[-1]
        for (x1, y1) in prev:
            closest = min(curr, key=lambda c: np.hypot(c[0]-x1, c[1]-y1)) if curr else None
            if closest:
                x2, y2 = closest
                dx = x2 - x1
                if abs(dx) > 1:
                    if dx > 0 and x1 < ENTRY_LINE_X <= x2:
                        self.people_inside += 1
                        self.entry_events.append("IN")
                    elif dx < 0 and x1 > ENTRY_LINE_X >= x2 and self.people_inside > 0:
                        self.people_inside -= 1
                        self.exit_events.append("OUT")
        return self.people_inside
