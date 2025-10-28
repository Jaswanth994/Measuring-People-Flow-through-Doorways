# visualization.py
import numpy as np
import cv2

def visualize(frame, mask, blobs, inside_count):
    img = cv2.normalize(frame, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    img = cv2.applyColorMap(cv2.resize(img, (320, 320), interpolation=cv2.INTER_NEAREST), cv2.COLORMAP_JET)

    for (x, y) in blobs:
        cv2.circle(img, (x*40+20, y*40+20), 10, (255, 255, 255), -1)

    cv2.putText(img, f"Inside: {inside_count}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.imshow("Grid-EYE Feed", img)
    cv2.waitKey(1)
