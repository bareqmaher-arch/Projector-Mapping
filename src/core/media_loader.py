import cv2
import os
import numpy as np
from PyQt6.QtGui import QImage, QPixmap

class MediaItem:
    def __init__(self, path):
        self.path = path
        if path:
            self.name = os.path.basename(path)
        else:
            self.name = "Empty Surface"
            
        self.type = "unknown"
        self.texture_id = None  # OpenGL Texture ID
        self.texture_uploaded = False # Flag to check if texture is uploaded
        self.width = 0
        self.height = 0
        self.image = None
        self.cap = None
        self.current_frame_data = None
        self.texture_version = 0
        self.needs_upload = False
        
        if self.path is None:
            self.type = "placeholder"
            self.create_placeholder_texture()
        elif self.path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
            self.type = "image"
            self.image = cv2.imread(self.path)
            if self.image is not None:
                self.image = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
                self.height, self.width, _ = self.image.shape
                self.current_frame_data = self.image
                self.needs_upload = True
        
        elif self.path.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')):
            self.type = "video"
            self.cap = cv2.VideoCapture(self.path)
            self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.fps = self.cap.get(cv2.CAP_PROP_FPS)
            self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
    def create_placeholder_texture(self):
        # Create a 512x512 checkerboard/grid texture
        self.width = 512
        self.height = 512
        
        # Create grid image
        img = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        # Draw checkerboard
        cell_size = 64
        for y in range(0, self.height, cell_size):
            for x in range(0, self.width, cell_size):
                if (x // cell_size + y // cell_size) % 2 == 0:
                    cv2.rectangle(img, (x, y), (x+cell_size, y+cell_size), (40, 40, 40), -1)
                else:
                    cv2.rectangle(img, (x, y), (x+cell_size, y+cell_size), (80, 80, 80), -1)
        
        # Draw grid lines
        for i in range(0, self.width, cell_size):
            cv2.line(img, (i, 0), (i, self.height), (100, 100, 100), 1)
        for i in range(0, self.height, cell_size):
            cv2.line(img, (0, i), (self.width, i), (100, 100, 100), 1)
            
        # Draw X
        cv2.line(img, (0, 0), (self.width, self.height), (100, 100, 100), 2)
        cv2.line(img, (self.width, 0), (0, self.height), (100, 100, 100), 2)
        
        # Add Text "Empty Surface"
        cv2.putText(img, "Empty Surface", (50, 256), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (200, 200, 200), 2)
        
        self.current_frame_data = img
        self.needs_upload = True

    def update_frame(self):
        """Advances the video to the next frame. Should be called once per tick."""
        if self.type == "video":
            if self.cap is None or not self.cap.isOpened():
                return
            ret, frame = self.cap.read()
            if not ret:
                # Loop video
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = self.cap.read()
            if ret:
                self.current_frame_data = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                self.texture_version += 1
                self.needs_upload = True
                return True
        return False

    def get_frame(self):
        """Returns the current cached frame."""
        return self.current_frame_data

    def release(self):
        if self.type == "video" and self.cap:
            self.cap.release()
