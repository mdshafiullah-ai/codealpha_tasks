"""
Real-Time Object Detection & Tracking
======================================
Pipeline: Video/Webcam → OpenCV → YOLOv8 Detection → Deep SORT Tracking → Real-Time Output

Uses Ultralytics YOLOv8 for detection and deep-sort-realtime for multi-object tracking.
Each tracked object is assigned a persistent unique ID that remains stable across frames.

Usage:
    python app.py                       # webcam (device 0)
    python app.py --source 1            # webcam (device 1)
    python app.py --source video.mp4    # video file
    python app.py --model yolov8s.pt    # use a different YOLO model
    python app.py --conf 0.5            # set confidence threshold
"""

import argparse
import sys
import time
from pathlib import Path

import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import cv2
import numpy as np

from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort


# ──────────────────────────────────────────────
# Colour palette for tracking IDs (25 distinct)
# ──────────────────────────────────────────────
PALETTE = [
    (235,  65,  54),   # red
    ( 46, 204, 113),   # emerald
    ( 52, 152, 219),   # blue
    (243, 156,  18),   # orange
    (155,  89, 182),   # purple
    ( 26, 188, 156),   # turquoise
    (231,  76,  60),   # alizarin
    ( 41, 128, 185),   # belize
    (241, 196,  15),   # sunflower
    (142,  68, 173),   # wisteria
    ( 22, 160, 133),   # green sea
    (230, 126,  34),   # carrot
    ( 44,  62,  80),   # midnight
    (127, 140, 141),   # concrete
    ( 39, 174,  96),   # nephritis
    (192,  57,  43),   # pomegranate
    (211,  84,   0),   # pumpkin
    (  0, 188, 212),   # cyan
    (255, 193,   7),   # amber
    (103,  58, 183),   # deep purple
    (  0, 150, 136),   # teal
    (255,  87,  34),   # deep orange
    ( 63,  81, 181),   # indigo
    (205, 220,  57),   # lime
    (121,  85,  72),   # brown
]


def colour_for_id(track_id: int) -> tuple:
    """Return a deterministic BGR colour for a given tracking ID."""
    rgb = PALETTE[track_id % len(PALETTE)]
    return (rgb[2], rgb[1], rgb[0])  # convert to BGR for OpenCV


# ──────────────────────────────────────────────
# Drawing helpers
# ──────────────────────────────────────────────
def draw_rounded_rect(img, pt1, pt2, colour, radius=8, thickness=2):
    """Draw a rectangle with rounded corners."""
    x1, y1 = pt1
    x2, y2 = pt2

    # Draw straight edges
    cv2.line(img, (x1 + radius, y1), (x2 - radius, y1), colour, thickness)
    cv2.line(img, (x1 + radius, y2), (x2 - radius, y2), colour, thickness)
    cv2.line(img, (x1, y1 + radius), (x1, y2 - radius), colour, thickness)
    cv2.line(img, (x2, y1 + radius), (x2, y2 - radius), colour, thickness)

    # Draw corner arcs
    cv2.ellipse(img, (x1 + radius, y1 + radius), (radius, radius), 180, 0, 90, colour, thickness)
    cv2.ellipse(img, (x2 - radius, y1 + radius), (radius, radius), 270, 0, 90, colour, thickness)
    cv2.ellipse(img, (x1 + radius, y2 - radius), (radius, radius),  90, 0, 90, colour, thickness)
    cv2.ellipse(img, (x2 - radius, y2 - radius), (radius, radius),   0, 0, 90, colour, thickness)


def draw_label_badge(img, text, origin, bg_colour, font_scale=0.55, thickness=1):
    """Draw a text label with a filled rounded-rectangle background."""
    font = cv2.FONT_HERSHEY_SIMPLEX
    (tw, th), baseline = cv2.getTextSize(text, font, font_scale, thickness)
    x, y = origin
    pad_x, pad_y = 8, 5

    # Background pill
    top_left = (x, y - th - 2 * pad_y)
    bot_right = (x + tw + 2 * pad_x, y)
    overlay = img.copy()
    cv2.rectangle(overlay, top_left, bot_right, bg_colour, cv2.FILLED)
    cv2.addWeighted(overlay, 0.85, img, 0.15, 0, img)

    # White text
    cv2.putText(
        img, text,
        (x + pad_x, y - pad_y),
        font, font_scale, (255, 255, 255), thickness, cv2.LINE_AA,
    )


def draw_track(frame, bbox, track_id, label, confidence):
    """Draw a single tracked object: bounding box + label badge + ID badge."""
    x1, y1, x2, y2 = map(int, bbox)
    colour = colour_for_id(track_id)

    # Bounding box with rounded corners
    draw_rounded_rect(frame, (x1, y1), (x2, y2), colour, radius=6, thickness=2)

    # Corner accents (small L-shapes for a modern look)
    accent_len = 18
    t = 3
    cv2.line(frame, (x1, y1), (x1 + accent_len, y1), colour, t)
    cv2.line(frame, (x1, y1), (x1, y1 + accent_len), colour, t)
    cv2.line(frame, (x2, y1), (x2 - accent_len, y1), colour, t)
    cv2.line(frame, (x2, y1), (x2, y1 + accent_len), colour, t)
    cv2.line(frame, (x1, y2), (x1 + accent_len, y2), colour, t)
    cv2.line(frame, (x1, y2), (x1, y2 - accent_len), colour, t)
    cv2.line(frame, (x2, y2), (x2 - accent_len, y2), colour, t)
    cv2.line(frame, (x2, y2), (x2, y2 - accent_len), colour, t)

    # Class label + confidence badge (top of box)
    class_text = f"{label} {confidence:.0%}"
    draw_label_badge(frame, class_text, (x1, y1), colour)

    # Tracking ID badge (bottom-left of box)
    id_text = f"ID: {track_id}"
    draw_label_badge(frame, id_text, (x1, y2 + 22), colour, font_scale=0.5)


def draw_hud(frame, fps, num_tracks, model_name):
    """Draw a translucent heads-up display overlay with stats."""
    h, w = frame.shape[:2]

    # Semi-transparent dark bar at the top
    bar_h = 40
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, bar_h), (20, 20, 20), cv2.FILLED)
    cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(
        frame,
        f"Object Detection & Tracking  |  {model_name}  |  FPS: {fps:.1f}  |  Tracked: {num_tracks}",
        (12, 27), font, 0.55, (200, 220, 255), 1, cv2.LINE_AA,
    )

    # Hotkey hint at the bottom
    hint = "Press 'Q' to quit  |  'P' to pause  |  'S' to screenshot"
    (tw, th), _ = cv2.getTextSize(hint, font, 0.42, 1)
    cv2.putText(
        frame, hint,
        (w - tw - 12, h - 10), font, 0.42, (160, 160, 160), 1, cv2.LINE_AA,
    )


# ──────────────────────────────────────────────
# Core pipeline
# ──────────────────────────────────────────────
def parse_args():
    parser = argparse.ArgumentParser(
        description="Real-Time Object Detection & Tracking (YOLOv8 + Deep SORT)",
    )
    parser.add_argument(
        "--source", type=str, default="0",
        help="Video source: webcam index (0, 1, …) or path to video file",
    )
    parser.add_argument(
        "--model", type=str, default="yolov8n.pt",
        help="YOLO model to load (e.g. yolov8n.pt, yolov8s.pt, yolov8m.pt)",
    )
    parser.add_argument(
        "--conf", type=float, default=0.35,
        help="Minimum detection confidence threshold (default: 0.35)",
    )
    parser.add_argument(
        "--max-age", type=int, default=30,
        help="Deep SORT: max frames to keep a lost track alive (default: 30)",
    )
    parser.add_argument(
        "--save", type=str, default=None,
        help="Path to save the output video (e.g. output.mp4)",
    )
    return parser.parse_args()


def open_video_source(source_str: str):
    """Open a webcam (by index) or video file. Returns a cv2.VideoCapture."""
    # Try to interpret source as an integer (webcam device index)
    try:
        device_index = int(source_str)
        cap = cv2.VideoCapture(device_index)
        if not cap.isOpened():
            print(f"[ERROR] Cannot open webcam device {device_index}.")
            print("        Make sure your webcam is connected and not in use by another app.")
            sys.exit(1)
        print(f"[INFO] Opened webcam (device {device_index})")
        return cap
    except ValueError:
        pass

    # Treat source as a file path
    path = Path(source_str)
    if not path.is_file():
        print(f"[ERROR] Video file not found: {source_str}")
        sys.exit(1)

    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        print(f"[ERROR] Cannot open video file: {source_str}")
        sys.exit(1)

    print(f"[INFO] Opened video file: {path.name}")
    return cap


def run():
    args = parse_args()

    # ── Load YOLO model ────────────────────────
    print(f"[INFO] Loading YOLO model: {args.model} …")
    try:
        model = YOLO(args.model)
    except Exception as exc:
        print(f"[ERROR] Failed to load YOLO model '{args.model}': {exc}")
        sys.exit(1)

    # Class names from the model
    class_names = model.names  # dict: {0: 'person', 1: 'bicycle', …}
    model_label = Path(args.model).stem.upper()
    print(f"[INFO] Model loaded — {len(class_names)} classes")

    # ── Initialise Deep SORT tracker ───────────
    tracker = DeepSort(
        max_age=args.max_age,
        n_init=3,                     # require 3 consecutive detections to confirm
        nms_max_overlap=1.0,
        max_cosine_distance=0.2,
        nn_budget=100,
        override_track_class=None,
        embedder="mobilenet",         # lightweight appearance embedder
        half=True,
        bgr=True,
        embedder_gpu=True,
    )
    print("[INFO] Deep SORT tracker initialised")

    # ── Open video source ──────────────────────
    cap = open_video_source(args.source)
    frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    src_fps = cap.get(cv2.CAP_PROP_FPS) or 30

    # Optional output writer
    writer = None
    if args.save:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(args.save, fourcc, src_fps, (frame_w, frame_h))
        print(f"[INFO] Recording output → {args.save}")

    print("[INFO] Starting detection & tracking loop … Press 'Q' to quit.\n")

    # ── Main loop ──────────────────────────────
    fps = 0.0
    frame_count = 0
    paused = False

    while True:
        if not paused:
            t_start = time.perf_counter()
            ret, frame = cap.read()
            if not ret:
                # For video files, this means end-of-file
                if not args.source.isdigit():
                    print("\n[INFO] End of video reached.")
                else:
                    print("\n[WARNING] Failed to grab frame from webcam.")
                break

            frame_count += 1

            # ── YOLOv8 inference ───────────────
            results = model.predict(
                frame,
                conf=args.conf,
                verbose=False,
                stream=False,
            )

            # ── Parse detections for Deep SORT ─
            # deep-sort-realtime expects a list of:
            #   ([left, top, w, h], confidence, class_name)
            detections = []
            det_result = results[0]

            if det_result.boxes is not None and len(det_result.boxes):
                for box in det_result.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    conf = float(box.conf[0].cpu().numpy())
                    cls_id = int(box.cls[0].cpu().numpy())
                    cls_name = class_names.get(cls_id, str(cls_id))

                    bbox_ltwh = [float(x1), float(y1), float(x2 - x1), float(y2 - y1)]
                    detections.append((bbox_ltwh, conf, cls_name))

            # ── Deep SORT update ───────────────
            tracks = tracker.update_tracks(detections, frame=frame)

            # ── Draw confirmed tracks ──────────
            active_count = 0
            for track in tracks:
                if not track.is_confirmed():
                    continue
                active_count += 1

                track_id = track.track_id
                ltrb = track.to_ltrb()  # (left, top, right, bottom)
                det_class = track.det_class if track.det_class else "?"
                det_conf = track.det_conf if track.det_conf is not None else 0.0

                draw_track(frame, ltrb, int(track_id), det_class, det_conf)

            # ── FPS calculation (exponential moving average) ─
            elapsed = time.perf_counter() - t_start
            instant_fps = 1.0 / max(elapsed, 1e-6)
            fps = 0.9 * fps + 0.1 * instant_fps if frame_count > 1 else instant_fps

            # ── HUD overlay ────────────────────
            draw_hud(frame, fps, active_count, model_label)

            # ── Display / save ─────────────────
            cv2.imshow("Object Detection & Tracking", frame)
            if writer:
                writer.write(frame)

        # ── Keyboard handling ──────────────────
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q") or key == ord("Q") or key == 27:   # Q or ESC
            print("\n[INFO] Quit requested.")
            break
        elif key == ord("p") or key == ord("P"):
            paused = not paused
            state = "PAUSED" if paused else "RESUMED"
            print(f"[INFO] {state}")
        elif key == ord("s") or key == ord("S"):
            screenshot_path = f"screenshot_{frame_count:06d}.png"
            cv2.imwrite(screenshot_path, frame)
            print(f"[INFO] Screenshot saved → {screenshot_path}")

    # ── Cleanup ────────────────────────────────
    cap.release()
    if writer:
        writer.release()
    cv2.destroyAllWindows()
    print(f"[INFO] Processed {frame_count} frames. Goodbye!")


if __name__ == "__main__":
    run()
