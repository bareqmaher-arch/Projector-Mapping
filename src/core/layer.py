import numpy as np
import cv2

class Layer:
    def __init__(self, media_item):
        self.media = media_item
        if media_item:
            self.name = media_item.name
        else:
            self.name = "Group"
            
        self.visible = True
        self.opacity = 1.0
        self.blend_mode = "Normal"
        
        # Grouping
        self.parent = None
        self.children = [] # List of Layer objects
        self.span_group_media = False # If True, media is mapped across all children based on screen position
        
        # Grid Warp / Mesh Properties
        self.grid_rows = 2
        self.grid_cols = 2
        
        # Masking
        self.masks = [] # List of lists of points: [[(x,y), ...], ...]
        
        # Normalized coordinates (0.0 to 1.0)
        self.source_corners = np.array([
            [0.0, 0.0],
            [1.0, 0.0],
            [1.0, 1.0],
            [0.0, 1.0]
        ], dtype=np.float32)
        
        # Screen coordinates (pixels) - initialized when added to canvas
        # dest_corners is now just a helper for initialization/bounds
        # mesh_points is the source of truth: shape (rows, cols, 2)
        self.mesh_points = np.zeros((2, 2, 2), dtype=np.float32)
        
        # Default initialization (will be overwritten by canvas)
        self.mesh_points[0, 0] = [100, 100]
        self.mesh_points[0, 1] = [500, 100]
        self.mesh_points[1, 0] = [100, 400]
        self.mesh_points[1, 1] = [500, 400]
        
        # Keep dest_corners for backward compat/easy access to corners
        self.dest_corners = np.array([
            [100.0, 100.0],
            [500.0, 100.0],
            [500.0, 400.0],
            [100.0, 400.0]
        ], dtype=np.float32)
        
        self.selected_corner_index = -1

    def add_child(self, layer):
        if layer not in self.children:
            self.children.append(layer)
            layer.parent = self

    def remove_child(self, layer):
        if layer in self.children:
            self.children.remove(layer)
            layer.parent = None

    def set_media(self, media_item):
        """Replaces the media item for this layer."""
        self.media = media_item
        if self.name == "Empty Surface":
            self.name = media_item.name
        
        # Reset texture upload flag so it gets re-uploaded
        if self.media:
            self.media.needs_upload = True

    def to_dict(self):
        data = {
            "name": self.name,
            "media_path": self.media.path if self.media else None,
            "opacity": self.opacity,
            "visible": self.visible,
            "blend_mode": self.blend_mode,
            "grid_rows": self.grid_rows,
            "grid_cols": self.grid_cols,
            "mesh_points": self.mesh_points.tolist(),
            "masks": self.masks,
            "span_group_media": self.span_group_media,
            "children": [child.to_dict() for child in self.children]
        }
        return data

    @staticmethod
    def from_dict(data, media_loader_class):
        from core.media_loader import MediaItem # Local import to avoid circular dependency
        
        media_path = data.get("media_path")
        if media_path:
            media_item = MediaItem(media_path)
        else:
            media_item = None # Could be a group container or placeholder
            
        layer = Layer(media_item)
        layer.name = data.get("name", layer.name)
        layer.opacity = data.get("opacity", 1.0)
        layer.visible = data.get("visible", True)
        layer.blend_mode = data.get("blend_mode", "Normal")
        
        layer.grid_rows = data.get("grid_rows", 2)
        layer.grid_cols = data.get("grid_cols", 2)
        layer.masks = data.get("masks", [])
        layer.span_group_media = data.get("span_group_media", False)
        
        if "mesh_points" in data:
            layer.mesh_points = np.array(data["mesh_points"], dtype=np.float32)
            # Update dest_corners from mesh corners
            layer.dest_corners = np.array([
                layer.mesh_points[0, 0],
                layer.mesh_points[0, -1],
                layer.mesh_points[-1, -1],
                layer.mesh_points[-1, 0]
            ], dtype=np.float32)
        elif "dest_corners" in data:
            # Legacy support
            corners = np.array(data["dest_corners"], dtype=np.float32)
            layer.dest_corners = corners
            layer.mesh_points = np.zeros((2, 2, 2), dtype=np.float32)
            layer.mesh_points[0, 0] = corners[0]
            layer.mesh_points[0, 1] = corners[1]
            layer.mesh_points[1, 1] = corners[2]
            layer.mesh_points[1, 0] = corners[3]
            
        # Load children
        children_data = data.get("children", [])
        for child_data in children_data:
            child_layer = Layer.from_dict(child_data, media_loader_class)
            layer.add_child(child_layer)
            
        return layer

    def set_grid_size(self, rows, cols):
        if rows < 2 or cols < 2:
            return
        
        if rows == self.grid_rows and cols == self.grid_cols:
            return
            
        # Interpolate existing mesh to new size
        # Treat mesh_points as an image of shape (rows, cols, 2)
        # Use cv2.resize with linear interpolation
        new_mesh = cv2.resize(self.mesh_points, (cols, rows), interpolation=cv2.INTER_LINEAR)
        
        self.mesh_points = new_mesh
        self.grid_rows = rows
        self.grid_cols = cols

    def get_texture_id(self):
        return self.media.texture_id

    def set_texture_id(self, tex_id):
        self.media.texture_id = tex_id

    def is_uploaded(self):
        return self.media.texture_uploaded

    def set_uploaded(self, val):
        self.media.texture_uploaded = val

    def get_frame(self):
        return self.media.get_frame()

    def update_corners(self, index, x, y):
        # Index can now be a tuple (row, col) or flat index?
        # Canvas handles the mapping. Here we expect (row, col) or we update dest_corners for compat.
        pass

    def hit_test_corners(self, x, y, radius=10):
        # Check all mesh points
        for r in range(self.grid_rows):
            for c in range(self.grid_cols):
                px, py = self.mesh_points[r, c]
                dx = x - px
                dy = y - py
                if dx*dx + dy*dy <= radius*radius:
                    return (r, c)
        return -1

    def hit_test_masks(self, x, y, radius=10):
        for m_idx, mask in enumerate(self.masks):
            for p_idx, point in enumerate(mask):
                px, py = point
                dx = x - px
                dy = y - py
                if dx*dx + dy*dy <= radius*radius:
                    return (m_idx, p_idx)
        return None
