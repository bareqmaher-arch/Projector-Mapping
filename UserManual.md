# Projector Mapping Studio - User Manual

## Overview
Projector Mapping Studio is a professional-grade projection mapping application designed for real-time performance. It allows you to map images and videos onto physical surfaces using advanced calibration tools.

## Features
- **Multi-Monitor Support**: Project to any connected display in full screen.
- **Layer-Based Composition**: Manage multiple media items as layers.
- **Grid Warp (Mesh Mapping)**: Precise curved surface calibration.
- **Masking**: Hide unwanted areas with geometric masks.
- **Blend Modes**: Composite layers using Add, Multiply, Screen, etc.
- **Media Support**: Import Images (JPG, PNG) and Videos (MP4, AVI).
- **Project Management**: Save and Load projects (JSON format).

## Getting Started

### 1. Installation
Run the installer or build from source:
```bash
python src/main.py
```

### 2. Interface Overview
- **Canvas (Center)**: The main working area where you position and warp your layers.
- **Layer Panel (Left)**: Manage your layer stack.
- **Property Panel (Right)**: Adjust properties for the selected layer.
- **Toolbar (Top)**: Quick access to common actions.

### 3. Workflow

#### Importing Media
1. Go to `File > Import Media` or click the Import icon in the toolbar.
2. Select an image or video file.
3. The media will be added as a new layer.

#### Adding Empty Surfaces
1. Click the **Add Quad** button in the toolbar.
2. A new empty surface (grid pattern) will be added.
3. Use the **Assign Media** button in the Property Panel to load an image/video onto this surface later.

#### Layer Grouping
1. Select multiple layers in the **Layer Panel** (hold Ctrl/Cmd).
2. Click the **Group** button at the bottom of the panel.
3. The selected layers will be moved into a new Group.
4. **Unified Media**: Check the **Span Media** box in the Property Panel to map a single media item across all layers in the group based on their screen position.

#### Calibration (Mapping)
1. Select a layer in the **Layer Panel**.
2. **Move**: Drag the layer to position it.
3. **Snapping**: Toggle the **Magnet/Snap** button in the toolbar to snap mesh points to other layers' points for seamless alignment.
4. **Grid Warp**:
   - In the **Property Panel**, adjust **Grid Size** (Rows/Cols) to add more control points.
   - Drag the yellow mesh points on the Canvas to warp the image onto curved surfaces.

#### Masking
1. Select a layer.
2. In the **Property Panel**, click **Add Rect Mask**.
3. A magenta mask will appear. Drag its points to define the area to hide (cut out).
4. Click **Clear Masks** to remove all masks from the layer.

#### Blending
1. Select a layer.
2. In the **Property Panel**, change the **Blend Mode** (e.g., Screen, Add, Multiply).
3. This affects how the layer blends with layers beneath it.

#### Multi-Monitor Output
1. Press `F11` or go to `View > Toggle Output Window`.
2. Select the target display from the list.
3. The Output Window will open full-screen on the selected display, showing the final composition without UI overlays.

### 4. Saving/Loading
- `File > Save Project`: Saves your current layout, warp settings, and masks to a `.proj` file.
- `File > Open Project`: Loads a previously saved project.

## Tips
- Use **Grid Warp** with a 3x3 or 4x4 grid for mapping onto cylinders or corners.
- **Screen** blend mode is great for removing black backgrounds from video effects.
- Ensure your secondary display is set to "Extend" mode in Windows Display Settings.
