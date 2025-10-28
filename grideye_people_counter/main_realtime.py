# main_realtime.py
import cv2
import time
from background_model import build_background
from sensor_interface import GridEyeSensor
from people_counter import detect_people
from motion_tracker import MotionTracker
from visualization import visualize
from utils import smooth_background
from config import FRAME_INTERVAL

def main():
    bg = build_background()
    sensor = GridEyeSensor()
    tracker = MotionTracker()
    print("[INFO] Starting real-time monitoring...")

    while True:
        frame = sensor.read_frame()
        blobs, mask = detect_people(frame, bg)
        inside = tracker.update(blobs)
        visualize(frame, mask, blobs, inside)
        bg = smooth_background(bg, frame)

        print(f"[INFO] People inside: {inside}")
        time.sleep(FRAME_INTERVAL)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Exiting...")
        cv2.destroyAllWindows()
