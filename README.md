# FlipPlayer

**FlipPlayer** – A flexible video player that lets you play forward, backward, record segments, and re-encode them while preserving original timing.  

---

## 🎯 Usage Scenarios
- 🎬 **Research / Teaching**: Inspect videos frame by frame, compare details before and after an event.  
- 🏀 **Sports Analysis**: Instant replay and reverse playback to examine movements in detail (e.g., checking for fouls).  
- 😂 **Creative Remixing**: Quickly capture clips, reverse them, and create memes or funny edits.  

---

## 🖼️ Demo
![image](./data/demo.gif)
<table border="0">
  <tr>
    <td align="center">Original Media</td>
    <td align="center">Re-encoded Result</td>
  </tr>
  <tr>
    <td align="center"><img src="https://raw.githubusercontent.com/kctaipei/FlipPlayer/main/data/input.gif" width="300"></td>
    <td align="center"><img src="https://raw.githubusercontent.com/kctaipei/FlipPlayer/main/data/output.gif" width="300"></td>
  </tr>
</table>
Media source: [link](https://pixabay.com/videos/fight-exercise-fitness-sport-203719)

---

## ✨ Features
- 🎞️ **Forward / Backward Playback**  
  Smooth, frame-accurate playback in both directions.  
- 🎚️ **Interactive Control**  
  - Play / Pause buttons  
  - Switch between playback modes  
  - Slider to jump to any frame  
- ⏺️ **Recording Mode**  
  Capture selected playback sequences (forward, backward, or mixed) as a new video.  
- ⚡ **Frame-level Precision**  
  Uses I-frame decoding and frame index tracking for accurate reverse navigation.  
- 💾 **Efficient Memory Usage**  
  Loads only the necessary frames into memory instead of buffering the entire video.  

---

## 📦 Installation
Install the required dependencies:
```bash
pip install -r requirements.txt
```
Requirements include:
- OpenCV
- PyAV (FFmpeg for Python)
- ipywidgets (for Jupyter UI)

---

## 🚀 Usage
Inside [main.ipynb](https://github.com/kctaipei/FlipPlayer/blob/main/main.ipynb), you can quickly set up and run the player:
```python
from src.player import Player
from src.ui import UI

video_path = 'data/input.mp4'

player = Player(video_path)
ui = UI(player)
ui.display()

player.start()
```
This will load a video, show the interactive controls, and allow you to:
- ▶ Play forward
- ⏮ Play backward
- ⏸ Pause
- ⏺ Record and re-encode selected clips
- 📍 Navigate frames using the slider

---

## 🏗️ Architecture
```
FlipPlayer/
├── src/
│ ├── player.py   # Core playback state engine
│ └── ui.py       # Jupyter UI widgets
├── data/
└── main.ipynb    # Interactive demo / entry point
```
- Player → Maintains playback state (PLAY_FORWARD, PLAY_BACKWARD, PAUSE, RECORD) and frame index tracking.
- UI → Contains buttons, slider and label that communicate with the player.

---

## 🧩 Challenges & Solutions
- 🔄 Reverse Playback
  - Problem: OpenCV cannot seek frames backward.
  - Solution: Locate the nearest previous I-frame, then decode forward until the target frame.
- ⏱ Preserving Original Timing
  - Problem: MP4 requires strictly monotonic PTS values.
  - Solution: Extract pkt_pts via ffprobe (PyAV), compute frame durations, and accumulate correctly during re-encode.

---

## 📌 Roadmap
- 🎵 Support audio tracks in re-encode
- ⏩ Add playback speed control
- 🌐 Web-based UI

---

## 📜 License
MIT License
