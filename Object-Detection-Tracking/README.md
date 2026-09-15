# 🎯 Real-Time Object Detection & Tracking

A polished, real-time object detection and multi-object tracking application built with **YOLOv8** and **Deep SORT**.

Each detected object is assigned a **persistent tracking ID** that remains stable as long as the object stays in the scene — even when it is briefly occluded or overlapping with other objects.

---

## 🏗️ Pipeline

```
Video / Webcam
      │
      ▼
   OpenCV  ──►  YOLOv8 Detection  ──►  Deep SORT Tracking  ──►  Real-Time Output
                 (bounding boxes,        (persistent IDs,         (annotated video
                  class labels,           re-identification)       with HUD overlay)
                  confidence)
```

## ✨ Features

| Feature | Details |
|---|---|
| **Detection** | YOLOv8 (nano / small / medium — configurable) via Ultralytics |
| **Tracking** | Deep SORT with MobileNet appearance embedder for re-ID |
| **Visual output** | Rounded bounding boxes, corner accents, label + ID badges, translucent HUD |
| **Input** | Webcam (any device index) or video file (`.mp4`, `.avi`, `.mkv`, …) |
| **Output** | Optional recording to `.mp4` |
| **Controls** | `Q` quit · `P` pause/resume · `S` screenshot |
| **Error handling** | Graceful messages for missing webcam, bad video path, model load failure |

---

## 📦 Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-username/CodeAlpha-Object-Detection-Tracking.git
cd CodeAlpha-Object-Detection-Tracking
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

> **Note:** The first run will automatically download the YOLOv8 model weights (~6 MB for `yolov8n.pt`) and the Deep SORT MobileNet embedder weights. An internet connection is required for the first run only.

---

## 🚀 Usage

### Webcam (default)

```bash
python app.py
```

### Specific webcam device

```bash
python app.py --source 1
```

### Video file

```bash
python app.py --source path/to/video.mp4
```

### Different YOLO model (larger = more accurate, slower)

```bash
python app.py --model yolov8s.pt   # small
python app.py --model yolov8m.pt   # medium
```

### Adjust confidence threshold

```bash
python app.py --conf 0.5
```

### Save output video

```bash
python app.py --source video.mp4 --save output.mp4
```

### All options

```
usage: app.py [-h] [--source SOURCE] [--model MODEL] [--conf CONF]
              [--max-age MAX_AGE] [--save SAVE]

options:
  --source   Video source: webcam index (0, 1, …) or path to video file
  --model    YOLO model to load (default: yolov8n.pt)
  --conf     Minimum detection confidence (default: 0.35)
  --max-age  Deep SORT max frames to keep a lost track (default: 30)
  --save     Path to save the output video
```

---

## 🔑 Keyboard Controls

| Key | Action |
|-----|--------|
| `Q` / `ESC` | Quit the application |
| `P` | Pause / Resume |
| `S` | Save a screenshot |

---

## 📁 Project Structure

```
CodeAlpha-Object-Detection-Tracking/
├── app.py              # Main application (detection + tracking loop)
├── requirements.txt    # Python dependencies
├── README.md           # This file
└── .gitignore          # Git ignore rules
```

---

## 🛠️ How It Works

1. **Frame Capture** — OpenCV reads frames from the webcam or video file.
2. **Object Detection** — Each frame is passed to YOLOv8, which returns bounding boxes, class labels, and confidence scores.
3. **Deep SORT Tracking** — Detections are fed to the Deep SORT tracker, which:
   - Uses a **Kalman filter** to predict object positions between frames.
   - Uses a **MobileNet appearance embedder** to compute visual features.
   - Matches detections to existing tracks using a combination of motion (IoU) and appearance (cosine distance).
   - Assigns a **unique, persistent ID** to each confirmed track.
4. **Visualisation** — Annotated frames are displayed in real time with bounding boxes, labels, confidence scores, tracking IDs, and an FPS counter.

---

## ⚠️ Troubleshooting

| Problem | Solution |
|---|---|
| `Cannot open webcam device 0` | Make sure your webcam is connected and not used by another app. Try `--source 1`. |
| Very low FPS | Use the lighter model: `--model yolov8n.pt`. Ensure GPU drivers (CUDA) are installed. |
| `ModuleNotFoundError` | Re-run `pip install -r requirements.txt` inside your virtual environment. |
| No window appears | On headless servers, OpenCV `imshow` won't work. Use `--save output.mp4` instead. |
| Tracking IDs keep changing | Lower `--conf` to avoid flickering detections, or increase `--max-age`. |

---

## 📜 License

This project is open-source and available under the [MIT License](LICENSE).
