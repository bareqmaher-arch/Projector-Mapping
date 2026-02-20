from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QSurfaceFormat
import OpenGL.GL as gl
import numpy as np
from core.layer import Layer

class ProjectionCanvas(QOpenGLWidget):
    def __init__(self, parent=None, layers=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Layers to render (shared list if provided)
        self.layers = layers if layers is not None else []
        self.selected_layer = None
        self.dragged_corner_index = -1
        self.dragged_mask_index = None
        self.active_edit_layer = None
        
        # Snapping
        self.snapping_enabled = False
        self.snap_threshold = 15.0 # pixels

    def initializeGL(self):
        gl.glClearColor(0.0, 0.0, 0.0, 1.0) # Black background for projection
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        gl.glEnable(gl.GL_TEXTURE_2D)
        
        # Stencil Buffer
        gl.glClearStencil(0)
        
        print("OpenGL Initialized")

    def resizeGL(self, w, h):
        gl.glViewport(0, 0, w, h)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        gl.glOrtho(0, w, h, 0, -1, 1)
        gl.glMatrixMode(gl.GL_MODELVIEW)

    def paintGL(self):
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT | gl.GL_STENCIL_BUFFER_BIT)
        gl.glLoadIdentity()
        
        for layer in self.layers:
            if layer.visible:
                self.draw_layer(layer)

    def draw_layer(self, layer, override_media=None, span_bounds=None):
        # Recursive drawing for groups
        if layer.children:
            # Check if this group should span media across children
            new_span_bounds = None
            if layer.media and getattr(layer, 'span_group_media', False):
                # Calculate bounding box of all visible children meshes
                all_points = []
                for child in layer.children:
                    if child.visible:
                        all_points.append(child.mesh_points.reshape(-1, 2))
                
                if all_points:
                    all_points_np = np.vstack(all_points)
                    min_x, min_y = np.min(all_points_np, axis=0)
                    max_x, max_y = np.max(all_points_np, axis=0)
                    # width/height must be non-zero
                    w = max(1.0, max_x - min_x)
                    h = max(1.0, max_y - min_y)
                    new_span_bounds = (min_x, min_y, w, h)

            for child in layer.children:
                if child.visible:
                    # Logic: If parent has media, child uses it.
                    # Pass it down as override_media
                    media_to_pass = layer.media if layer.media else override_media
                    
                    # Pass down span_bounds if calculated here, otherwise pass existing
                    bounds_to_pass = new_span_bounds if new_span_bounds else span_bounds
                    
                    self.draw_layer(child, override_media=media_to_pass, span_bounds=bounds_to_pass)
            return

        # Use override media if provided, else layer's own media
        media = override_media if override_media else layer.media

        # Skip if no media (unless it's a placeholder/grid)
        if not media:
            return

        if media.texture_id is None:
            # Generate texture ID
            media.texture_id = gl.glGenTextures(1)
            gl.glBindTexture(gl.GL_TEXTURE_2D, media.texture_id)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
        
        gl.glBindTexture(gl.GL_TEXTURE_2D, media.texture_id)
        
        # Check if we need to upload new texture data
        if media.needs_upload:
            frame = media.get_frame()
            if frame is not None:
                h, w, c = frame.shape
                gl.glPixelStorei(gl.GL_UNPACK_ALIGNMENT, 1)
                gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGB, w, h, 0, gl.GL_RGB, gl.GL_UNSIGNED_BYTE, frame)
                media.needs_upload = False
        
        # Apply opacity
        gl.glColor4f(1.0, 1.0, 1.0, layer.opacity)
        
        # Apply Blend Mode
        mode = getattr(layer, 'blend_mode', 'Normal')
        if mode == "Add":
            gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE)
        elif mode == "Multiply":
            gl.glBlendFunc(gl.GL_DST_COLOR, gl.GL_ZERO)
        elif mode == "Screen":
            gl.glBlendFunc(gl.GL_ONE, gl.GL_ONE_MINUS_SRC_COLOR)
        else:
            gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        
        # --- Stencil Masking Logic ---
        if layer.masks:
            gl.glClear(gl.GL_STENCIL_BUFFER_BIT)
            gl.glEnable(gl.GL_STENCIL_TEST)
            
            # Disable color write
            gl.glColorMask(gl.GL_FALSE, gl.GL_FALSE, gl.GL_FALSE, gl.GL_FALSE)
            
            # Always pass stencil test, replace value with 1
            gl.glStencilFunc(gl.GL_ALWAYS, 1, 0xFF)
            gl.glStencilOp(gl.GL_REPLACE, gl.GL_REPLACE, gl.GL_REPLACE)
            
            # Draw masks
            for mask in layer.masks:
                if len(mask) < 3: continue
                gl.glDisable(gl.GL_TEXTURE_2D)
                gl.glBegin(gl.GL_POLYGON)
                for mx, my in mask:
                    gl.glVertex3f(mx, my, 0.0)
                gl.glEnd()
                gl.glEnable(gl.GL_TEXTURE_2D)
            
            # Enable color write
            gl.glColorMask(gl.GL_TRUE, gl.GL_TRUE, gl.GL_TRUE, gl.GL_TRUE)
            
            # Draw content only where stencil == 1
            gl.glStencilFunc(gl.GL_EQUAL, 1, 0xFF)
            gl.glStencilOp(gl.GL_KEEP, gl.GL_KEEP, gl.GL_KEEP)
        else:
            gl.glDisable(gl.GL_STENCIL_TEST)
        
        # Draw Mesh Grid
        rows = layer.grid_rows
        cols = layer.grid_cols
        mesh = layer.mesh_points
        
        gl.glBegin(gl.GL_QUADS)
        for r in range(rows - 1):
            for c in range(cols - 1):
                # Vertex coordinates
                p00 = mesh[r, c]
                p01 = mesh[r, c+1]
                p11 = mesh[r+1, c+1]
                p10 = mesh[r+1, c]
                
                # Texture coordinates
                if span_bounds:
                    # UV based on screen position relative to span_bounds (min_x, min_y, w, h)
                    bx, by, bw, bh = span_bounds
                    u0 = (p00[0] - bx) / bw
                    v0 = (p00[1] - by) / bh
                    
                    u1 = (p01[0] - bx) / bw
                    v1 = (p01[1] - by) / bh
                    
                    u2 = (p11[0] - bx) / bw
                    v2 = (p11[1] - by) / bh
                    
                    u3 = (p10[0] - bx) / bw
                    v3 = (p10[1] - by) / bh
                else:
                    # Standard grid-based UV
                    u0 = c / (cols - 1)
                    v0 = r / (rows - 1)
                    u1 = (c + 1) / (cols - 1)
                    v1 = (r + 1) / (rows - 1)
                    u2 = (c + 1) / (cols - 1)
                    v2 = (r + 1) / (rows - 1)
                    u3 = c / (cols - 1)
                    v3 = (r + 1) / (rows - 1)
                
                # Top-Left
                gl.glTexCoord2f(u0, v0); gl.glVertex3f(p00[0], p00[1], 0.0)
                # Top-Right
                gl.glTexCoord2f(u1, v0); gl.glVertex3f(p01[0], p01[1], 0.0)
                # Bottom-Right
                gl.glTexCoord2f(u2, v2); gl.glVertex3f(p11[0], p11[1], 0.0)
                # Bottom-Left
                gl.glTexCoord2f(u3, v3); gl.glVertex3f(p10[0], p10[1], 0.0)
        gl.glEnd()
        
        gl.glDisable(gl.GL_STENCIL_TEST)
        
        # Reset Blend Mode for UI
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        
        # Draw UI handles if selected
        if layer == self.selected_layer:
            self.draw_handles(layer)

    def draw_handles(self, layer):
        if layer.children:
            for child in layer.children:
                self.draw_handles(child)
            return

        gl.glDisable(gl.GL_TEXTURE_2D)
        gl.glDisable(gl.GL_DEPTH_TEST) # Ensure handles are on top
        
        # Draw Mask Handles
        if layer.masks:
            gl.glColor3f(1.0, 0.0, 1.0) # Magenta for masks
            gl.glPointSize(8.0)
            
            for mask in layer.masks:
                gl.glBegin(gl.GL_POINTS)
                for mx, my in mask:
                    gl.glVertex3f(mx, my, 0.0)
                gl.glEnd()
                
                gl.glLineWidth(1.5)
                gl.glBegin(gl.GL_LINE_LOOP)
                for mx, my in mask:
                    gl.glVertex3f(mx, my, 0.0)
                gl.glEnd()
        
        gl.glColor3f(1.0, 1.0, 0.0) # Yellow handles
        gl.glPointSize(8.0)
        gl.glBegin(gl.GL_POINTS)
        
        rows = layer.grid_rows
        cols = layer.grid_cols
        
        for r in range(rows):
            for c in range(cols):
                p = layer.mesh_points[r, c]
                gl.glVertex3f(p[0], p[1], 0.0)
        gl.glEnd()
        
        # Draw mesh lines
        gl.glColor3f(0.5, 0.5, 0.5)
        gl.glLineWidth(1.0)
        
        # Horizontal lines
        for r in range(rows):
            gl.glBegin(gl.GL_LINE_STRIP)
            for c in range(cols):
                p = layer.mesh_points[r, c]
                gl.glVertex3f(p[0], p[1], 0.0)
            gl.glEnd()
            
        # Vertical lines
        for c in range(cols):
            gl.glBegin(gl.GL_LINE_STRIP)
            for r in range(rows):
                p = layer.mesh_points[r, c]
                gl.glVertex3f(p[0], p[1], 0.0)
            gl.glEnd()
        
        # Highlight outline
        gl.glColor3f(1.0, 1.0, 0.0)
        gl.glLineWidth(2.0)
        
        # Outer boundary
        gl.glBegin(gl.GL_LINE_LOOP)
        # Top edge
        for c in range(cols):
            p = layer.mesh_points[0, c]; gl.glVertex3f(p[0], p[1], 0.0)
        # Right edge
        for r in range(1, rows):
            p = layer.mesh_points[r, cols-1]; gl.glVertex3f(p[0], p[1], 0.0)
        # Bottom edge
        for c in range(cols-2, -1, -1):
            p = layer.mesh_points[rows-1, c]; gl.glVertex3f(p[0], p[1], 0.0)
        # Left edge
        for r in range(rows-2, 0, -1):
            p = layer.mesh_points[r, 0]; gl.glVertex3f(p[0], p[1], 0.0)
        gl.glEnd()
        
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glEnable(gl.GL_TEXTURE_2D)
    
    def add_layer(self, item):
        if not isinstance(item, Layer):
            # Assume it's MediaItem and wrap it
            layer = Layer(item)
        else:
            layer = item
            
        # Initialize corners to center if not set (or if loading new media)
        if np.all(layer.dest_corners == 0):
             cw = self.width()
             ch = self.height()
             aspect = layer.media.width / layer.media.height if layer.media.height > 0 else 1.0
             target_h = 400
             target_w = int(target_h * aspect)
             x = (cw - target_w) / 2
             y = (ch - target_h) / 2
             
             # Initialize mesh points
             layer.mesh_points = np.zeros((2, 2, 2), dtype=np.float32)
             layer.mesh_points[0, 0] = [x, y]
             layer.mesh_points[0, 1] = [x + target_w, y]
             layer.mesh_points[1, 1] = [x + target_w, y + target_h]
             layer.mesh_points[1, 0] = [x, y + target_h]
             
             # Initialize dest_corners for compatibility
             layer.dest_corners = np.array([
                 [x, y],
                 [x + target_w, y],
                 [x + target_w, y + target_h],
                 [x, y + target_h]
             ], dtype=np.float32)
        
        self.layers.append(layer)
        self.selected_layer = layer
        print(f"Added layer: {layer.name}")

    def mousePressEvent(self, event):
        x, y = event.position().x(), event.position().y()
        self.active_edit_layer = None
        
        # Check if we hit a corner of the selected layer
        if self.selected_layer:
            # If it's a group, check children
            targets = self.selected_layer.children if self.selected_layer.children else [self.selected_layer]
            
            for layer in targets:
                # Check masks first (on top)
                mask_hit = layer.hit_test_masks(x, y)
                if mask_hit:
                    self.dragged_mask_index = mask_hit
                    self.dragged_corner_index = -1
                    self.active_edit_layer = layer
                    return
                
                idx = layer.hit_test_corners(x, y)
                if idx != -1:
                    self.dragged_corner_index = idx
                    self.dragged_mask_index = None
                    self.active_edit_layer = layer
                    return
        
        # Check if we hit a layer body (simple bounding box for now)
        # Iterate in reverse to select top-most
        for layer in reversed(self.layers):
            if not layer.visible: continue
            # Approximate bounding box
            min_x = np.min(layer.mesh_points[:, :, 0])
            max_x = np.max(layer.mesh_points[:, :, 0])
            min_y = np.min(layer.mesh_points[:, :, 1])
            max_y = np.max(layer.mesh_points[:, :, 1])
            
            if min_x <= x <= max_x and min_y <= y <= max_y:
                self.selected_layer = layer
                self.dragged_corner_index = -1
                self.dragged_mask_index = None
                self.update()
                return
        
        self.selected_layer = None
        self.dragged_corner_index = -1
        self.dragged_mask_index = None
        self.update()

    def mouseMoveEvent(self, event):
        x = event.position().x()
        y = event.position().y()
        
        if self.selected_layer:
            # Check for dragging logic
            target = self.active_edit_layer if self.active_edit_layer else self.selected_layer
            
            # Mask dragging
            if self.dragged_mask_index:
                m_idx, p_idx = self.dragged_mask_index
                # TODO: Add snapping for masks too? For now just points.
                target.masks[m_idx][p_idx] = [x, y]
                self.update()
                return

            # Mesh point dragging
            if self.dragged_corner_index != -1:
                r, c = self.dragged_corner_index
                
                # Snapping Logic
                if self.snapping_enabled:
                    snapped_pos = self.snap_to_closest_point(x, y, target)
                    if snapped_pos:
                        x, y = snapped_pos
                
                target.mesh_points[r, c] = [x, y]
                
                # Update dest_corners if it's a corner (legacy compatibility)
                if r == 0 and c == 0:
                    target.dest_corners[0] = [x, y]
                elif r == 0 and c == target.grid_cols - 1:
                    target.dest_corners[1] = [x, y]
                elif r == target.grid_rows - 1 and c == target.grid_cols - 1:
                    target.dest_corners[2] = [x, y]
                elif r == target.grid_rows - 1 and c == 0:
                    target.dest_corners[3] = [x, y]
                    
                self.update()
                return
        
        # If no dragging, maybe hover effects?
        # super().mouseMoveEvent(event)

    def snap_to_closest_point(self, x, y, current_layer):
        best_dist = self.snap_threshold
        best_pos = None
        
        # Iterate all visible layers to find snap targets
        # Flatten structure if needed
        all_layers = []
        
        def collect_layers(layers_list):
            for l in layers_list:
                if l.visible:
                    all_layers.append(l)
                    if l.children:
                        collect_layers(l.children)
                        
        collect_layers(self.layers)
        
        for layer in all_layers:
            # Skip self (current layer being edited) to avoid self-snapping if undesired,
            # but user might want to snap to other points on same mesh?
            # Usually snapping to *other* objects is key.
            if layer == current_layer:
                continue
                
            # Check all mesh points of this layer
            # Vectorized distance check
            points = layer.mesh_points.reshape(-1, 2)
            dists = np.sqrt(np.sum((points - np.array([x, y]))**2, axis=1))
            
            min_idx = np.argmin(dists)
            min_dist = dists[min_idx]
            
            if min_dist < best_dist:
                best_dist = min_dist
                best_pos = points[min_idx]
        
        return best_pos

    def mouseReleaseEvent(self, event):
        self.dragged_corner_index = -1
        self.dragged_mask_index = None
        self.active_edit_layer = None
