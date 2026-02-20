# Projector Mapping Studio

A professional-grade, real-time Projection Mapping application for Windows, built with Python, PyQt6, and OpenGL.

## 🎯 Core Features

*   **Multi-Projector Support**: Create and manage multiple projection surfaces.
*   **Real-Time Calibration**: Corner pinning with draggable control points for precise geometric alignment.
*   **Grid Warp (Mesh Mapping)**: Precise warping for curved surfaces with adjustable grid size.
*   **Masking**: Geometric masking to hide unwanted projection areas.
*   **Blend Modes**: Professional blending (Add, Multiply, Screen) for layering effects.
*   **Media Support**: Import and play Images (PNG, JPG) and Videos (MP4, MOV, AVI) with real-time playback.
*   **Scene Management**: Save and load mapping configurations to JSON project files.
*   **Modern UI**: Dark-themed interface with dockable panels for Layers, Properties, and Timeline.
*   **Performance**: Hardware-accelerated rendering using OpenGL.

## 🛠️ Tech Stack

*   **Language**: Python 3.12+
*   **UI Framework**: PyQt6
*   **Graphics**: PyOpenGL (OpenGL 3.x/4.x)
*   **Computer Vision / Media**: OpenCV (headless)
*   **Math**: NumPy

## 📦 Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/your-repo/projector-mapping.git
    cd projector-mapping
    ```

2.  **Create a virtual environment** (recommended):
    ```bash
    python -m venv .venv
    .venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## 🚀 Usage

1.  **Run the application**:
    ```bash
    python src/main.py
    ```

2.  **Import Media**:
    *   Go to `File > Import Media...` or use `Ctrl+I`.
    *   Select an image or video file.

3.  **Mapping**:
    *   The media will appear as a quad on the canvas.
    *   Click on the quad to select it (yellow outline).
    *   Drag the **yellow corner points** to warp the projection onto your physical object.

4.  **Save Project**:
    *   Go to `File > Save Project` to save your configuration.

## 🏗️ Build Standalone Executable

To create a standalone `.exe` file for Windows:

```bash
pip install pyinstaller
pyinstaller --name "ProjectorMapping" --windowed --noconsole --add-data "src;src" src/main.py
```

The output will be in the `dist/ProjectorMapping` folder.

## 📂 Project Structure

*   `src/`: Source code
    *   `core/`: Core logic (Engine, Layer, MediaLoader)
    *   `ui/`: UI components (MainWindow, Canvas, Panels)
    *   `utils/`: Helper utilities
*   `assets/`: Icons and resources
*   `docs/`: Documentation
