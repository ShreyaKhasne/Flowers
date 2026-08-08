# ✨ Move Hand → Flowers Follow Your Hand (Python) 🌸

An interactive, real-time Python desktop application that tracks your hand movements using AI Computer Vision (**MediaPipe** + **OpenCV**) and turns your fingertips into glowing floral magic with **Pygame-CE** and **NumPy** physics!

---

## 🌟 Key Features

- 🖐️ **Real-Time Hand & Fingertip AI Tracking**:
  - Tracks 21 3D hand joints with Exponential Moving Average (EMA) position smoothing.
  - Multi-hand support with custom gesture recognition:
    - **Pinch (Thumb + Index)**: Spawns blooming flowers at fingertip locations.
    - **Open Palm Sweep**: Generates gust of wind and petal explosions.
    - **Hand Speed/Velocity**: Fast hand sweeps push floating petals away with wind turbulence physics.
- 🌸 **Procedural Flowers & Particle Engine**:
  - 5 Stunning Themes:
    1. **Sakura Blossom 🌸**: Delicate cherry blossom pink & white petals.
    2. **Neon Cyber Flora ✨**: Bioluminescent electric cyan, magenta, and purple light petals.
    3. **Golden Sunset 🌻**: Warm golden amber sunflowers and radiant sparks.
    4. **Mystic Lotus Lagoon 🪷**: Soft violet and aquamarine lotus blossoms.
    5. **Cosmic Sparkle 🌌**: Multi-spectrum stardust and radiant firework flora.
- 🎥 **Dual Display Modes**:
  - **Camera Mirror Overlay Mode**: Live webcam video feed overlaid with glowing neon hand skeletal lines and floral trails.
  - **Midnight Dark Canvas Mode**: Deep dark gradient background for maximum visual luminescence.
- 🎵 **Procedural Pentatonic Audio Chimes**:
  - Synthesizes sweet metallic chime audio notes when flowers bloom.

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.10+ (Tested up to Python 3.14 on Windows)
- Webcam (Optional: Mouse fallback mode available if no camera is attached)

### Running the Application

 run the main application:
```powershell
python app.py
```

---

## 🎮 Interactive Controls

| Key | Action |
| --- | --- |
| `1` - `5` | Switch Theme (*Sakura, Cyberpunk, Golden, Lotus, Cosmic*) |
| `C` | Toggle **Camera Overlay** vs. **Midnight Dark Canvas** |
| `H` | Toggle Glowing **Hand Skeleton Overlay** |
| `F` | **Flower Fireworks Explosion** |
| `R` | Reset/Clear Canvas |
| `SPACE` | Freeze / Pause Physics Animation |
| `S` | Save Screenshot (saved to `screenshots/` directory) |
| `Left Click` / `Pinch` | Bloom Flower at Cursor / Fingertip |
| `ESC` or `Q` | Quit Application |

---

## 🏗️ Architecture

- `app.py`: Main application loop, SDL window manager, OpenCV video capture, HUD overlay, hotkeys.
- `hand_tracker.py`: Real-time MediaPipe Hand landmark extractor, EMA position smoother, gesture engine.
- `flower_engine.py`: Procedural flower blooming generator, particle physics, wind turbulence, vine drawer.
- `sound_effects.py`: Procedural synth generating harmonic pentatonic chime sound effects.
