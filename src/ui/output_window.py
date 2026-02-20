from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout
from PyQt6.QtCore import Qt
from ui.canvas import ProjectionCanvas

class OutputWindow(QMainWindow):
    def __init__(self, layers, screen=None):
        super().__init__()
        self.setWindowTitle("Projector Output")
        
        # Remove window frame for full screen projection
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        
        # Create canvas with shared layers
        self.canvas = ProjectionCanvas(parent=self, layers=layers)
        
        # Central widget
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)
        self.setCentralWidget(container)
        
        # Move to target screen if provided
        if screen:
            self.setScreen(screen)
            # Move to the screen's geometry
            geo = screen.geometry()
            self.move(geo.x(), geo.y())
            self.resize(geo.width(), geo.height())
            self.showFullScreen()
        else:
            self.resize(800, 600)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
