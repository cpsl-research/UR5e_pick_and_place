#!/usr/bin/env python3
"""
Quick test: open D435i via V4L2 and detect ArUco markers.
Displays the camera feed with detected markers drawn on it.

Usage:
    python3 test_aruco_detection.py
"""

import cv2
import sys


def find_color_stream():
    """Try video devices to find the RealSense RGB color stream (640x480)."""
    for i in range(8):
        cap = cv2.VideoCapture(i, cv2.CAP_V4L2)
        if not cap.isOpened():
            continue
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
        ret, frame = cap.read()
        if ret and frame is not None:
            h, w = frame.shape[:2]
            channels = frame.shape[2] if len(frame.shape) == 3 else 1
            # Color stream is 3-channel and at least 640x480
            if channels == 3 and w >= 640 and h >= 400:
                print(f"Using /dev/video{i} ({w}x{h}, {channels}ch)")
                return cap
        cap.release()
    return None


def main():
    print("Looking for D435i color stream...")
    cap = find_color_stream()
    if cap is None:
        print("ERROR: Could not find color camera. Check USB connection.")
        sys.exit(1)

    # ArUco setup - 7x7 dictionary (OpenCV 4.6 API)
    aruco_dict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_7X7_100)
    aruco_params = cv2.aruco.DetectorParameters_create()

    print("Camera started. Looking for ArUco 7x7 markers (50mm, ID 0)...")
    print("Press 'q' to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detect markers
        corners, ids, rejected = cv2.aruco.detectMarkers(gray, aruco_dict, parameters=aruco_params)

        # Draw results
        display = frame.copy()
        if ids is not None:
            cv2.aruco.drawDetectedMarkers(display, corners, ids)
            for i, marker_id in enumerate(ids.flatten()):
                c = corners[i][0]
                cx = int(c[:, 0].mean())
                cy = int(c[:, 1].mean())
                text = f"ID:{marker_id} ({cx},{cy})"
                cv2.putText(display, text, (cx - 40, cy - 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                print(f"  Marker ID {marker_id} at pixel ({cx}, {cy})")
        else:
            cv2.putText(display, "No markers detected", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        cv2.imshow("ArUco Detection - Press 'q' to quit", display)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("Done.")


if __name__ == "__main__":
    main()
