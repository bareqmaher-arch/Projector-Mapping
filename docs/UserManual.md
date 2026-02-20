# User Manual - Projector Mapping Studio

## 1. Introduction
Projector Mapping Studio is a professional tool for mapping digital content onto real-world objects using standard projectors. It provides a flexible and efficient workflow for artists and designers.

## 2. Getting Started
### 2.1 Installation
1.  Download the latest release or clone the repository.
2.  Install Python 3.12+ and dependencies:
    `pip install -r requirements.txt`
3.  Run `python src/main.py`.

### 2.2 Interface Overview
*   **Left Panel**: **Layers & Objects** - Shows all active media layers.
*   **Center**: **Canvas** - The main projection area where you manipulate content.
*   **Right Panel**: **Properties** - Adjust settings for the selected layer (Opacity, Blend Mode).
*   **Bottom Panel**: **Timeline** - Controls for animation playback.

## 3. Workflow
### 3.1 Importing Media
1.  Go to `File > Import Media...` (Ctrl+I).
2.  Select an image (PNG, JPG) or video (MP4, MOV).
3.  The media will appear on the canvas and in the Layers panel.

### 3.2 Mapping & Calibration (Corner Pinning)
1.  **Select a Layer**: Click on the media quad in the canvas. A yellow outline will appear.
2.  **Adjust Corners**: Drag any of the 4 yellow corner points to warp the texture.
3.  **Real-Time Preview**: The texture updates instantly as you drag.
4.  **Tip**: Use this to align the projection with the corners of your physical object (e.g., a box, wall, or sculpture).

### 3.3 Layer Management
*   **Visibility**: Toggle layer visibility in the Layers panel (checkbox coming soon).
*   **Order**: Layers are rendered in the order they appear in the list (bottom to top).

### 3.4 Saving & Loading
1.  **Save Project**: `File > Save Project` (Ctrl+S). Saves the current layer configuration, including corner positions and media paths, to a `.proj` (JSON) file.
2.  **Open Project**: `File > Open Project` (Ctrl+O). Loads a previously saved project.

## 4. Advanced Features
*   **Video Playback**: Videos loop automatically.
*   **Performance**: Utilizes GPU acceleration for smooth playback even with multiple layers.

## 5. Troubleshooting
*   **Black Screen**: Ensure your graphics drivers are up to date.
*   **Media Not Loading**: Check if the file format is supported (OpenCV backend).
*   **Permissions**: Ensure the application has read access to your media files.
