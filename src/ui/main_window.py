from PyQt6.QtWidgets import (QMainWindow, QDockWidget, QWidget, 
                             QSplitter, QStatusBar, QToolBar, QMenu,
                             QFileDialog, QMessageBox, QTabWidget, QVBoxLayout,
                             QInputDialog, QApplication)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QIcon, QGuiApplication
import json

from ui.canvas import ProjectionCanvas
from ui.panels import LayerPanel, PropertyPanel, TimelinePanel
from ui.output_window import OutputWindow
from core.media_loader import MediaItem
from core.layer import Layer

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Projector Mapping Studio")
        self.resize(1280, 800)
        
        self.output_window = None
        
        # --- UI Setup ---
        self.setup_ui()
        
        # --- Master Timer for Animation Loop ---
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_loop)
        self.timer.start(16) # ~60 FPS
        
    def setup_ui(self):
        # 1. Central Widget (Canvas)
        self.canvas = ProjectionCanvas()
        
        # We wrap the canvas in a container to potentially add toolbars/controls
        central_container = QWidget()
        central_layout = QVBoxLayout(central_container)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.addWidget(self.canvas)
        
        self.setCentralWidget(central_container)
        
        # 2. Dock Widgets (Panels)
        self.create_docks()
        
        # 3. Menus & Toolbars
        self.create_menus()
        self.create_toolbar()
        
        # 4. Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def create_docks(self):
        # Left Panel: Layers / Scene Objects
        self.layer_dock = QDockWidget("Layers & Objects", self)
        self.layer_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.layer_panel = LayerPanel()
        
        # Connect layer selection
        self.layer_panel.layer_tree.itemSelectionChanged.connect(self.on_layer_selection_changed)
        
        # Connect Group/Delete signals
        self.layer_panel.groupRequested.connect(self.group_selected_layers)
        self.layer_panel.deleteRequested.connect(self.delete_selected_layers)
        
        self.layer_dock.setWidget(self.layer_panel)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.layer_dock)
        
        # Right Panel: Properties
        self.prop_dock = QDockWidget("Properties", self)
        self.prop_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.prop_panel = PropertyPanel()
        self.prop_panel.layerChanged.connect(self.canvas.update)
        self.prop_panel.assignMediaRequested.connect(self.on_assign_media_requested)
        self.prop_dock.setWidget(self.prop_panel)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.prop_dock)
        
        # Bottom Panel: Timeline
        self.timeline_dock = QDockWidget("Timeline", self)
        self.timeline_dock.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea | Qt.DockWidgetArea.TopDockWidgetArea)
        self.timeline_panel = TimelinePanel()
        self.timeline_dock.setWidget(self.timeline_panel)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.timeline_dock)

    def create_menus(self):
        menubar = self.menuBar()
        
        # File Menu
        file_menu = menubar.addMenu("&File")
        
        new_action = QAction("New Project", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_project)
        file_menu.addAction(new_action)
        
        open_action = QAction("Open Project...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_project)
        file_menu.addAction(open_action)
        
        save_action = QAction("Save Project", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_project)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        import_action = QAction("Import Media...", self)
        import_action.setShortcut("Ctrl+I")
        import_action.triggered.connect(self.import_media)
        file_menu.addAction(import_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View Menu
        view_menu = menubar.addMenu("&View")
        
        output_action = QAction("Toggle Output Window", self)
        output_action.setShortcut("F11")
        output_action.triggered.connect(self.toggle_output)
        view_menu.addAction(output_action)
        
        # Mapping Menu
        mapping_menu = menubar.addMenu("&Mapping")
        
        add_quad_action = QAction("Add Quad Surface", self)
        add_quad_action.triggered.connect(self.add_quad_surface)
        mapping_menu.addAction(add_quad_action)

    def create_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)
        
        # Add actions
        add_quad_action = QAction("Add Quad", self)
        add_quad_action.triggered.connect(self.add_quad_surface)
        toolbar.addAction(add_quad_action)
        
        toolbar.addSeparator()
        
        import_action = QAction("Import Media", self)
        import_action.triggered.connect(self.import_media)
        toolbar.addAction(import_action)
        
        toolbar.addSeparator()
        
        output_action = QAction("Output", self)
        output_action.triggered.connect(self.toggle_output)
        toolbar.addAction(output_action)
        
        toolbar.addSeparator()
        
        # Snapping Toggle
        self.snap_action = QAction("Magnet/Snap", self)
        self.snap_action.setCheckable(True)
        self.snap_action.setChecked(False)
        self.snap_action.toggled.connect(self.toggle_snapping)
        toolbar.addAction(self.snap_action)

    # --- Game Loop ---
    def update_loop(self):
        # Update all media
        needs_repaint = False
        for layer in self.canvas.layers:
            if layer.media.type == "video":
                updated = layer.media.update_frame()
                if updated:
                    needs_repaint = True
        
        # Trigger repaint if needed or always (for UI responsiveness)
        # We always update canvas to handle mouse interactions smoothly
        self.canvas.update()
        
        if self.output_window:
            self.output_window.canvas.update()
            
        # Also sync properties if selection changed (optional, could be event driven)
        if self.canvas.selected_layer:
            # We could update property panel here if we want real-time feedback
            pass

    # --- Actions ---
    def new_project(self):
        self.canvas.layers.clear()
        self.layer_panel.layer_tree.clear()
        self.status_bar.showMessage("New Project Created")

    def open_project(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Project", "", "Project Files (*.proj);;All Files (*)")
        if file_name:
            try:
                with open(file_name, 'r') as f:
                    data = json.load(f)
                
                self.new_project() # Clear current
                
                for layer_data in data.get("layers", []):
                    layer = Layer.from_dict(layer_data, None)
                    self.canvas.add_layer(layer)
                    
                self.update_layer_panel()
                
                self.status_bar.showMessage(f"Project loaded from {file_name}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load project: {e}")

    def save_project(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Project", "", "Project Files (*.proj);;All Files (*)")
        if file_name:
            data = {
                "layers": [layer.to_dict() for layer in self.canvas.layers]
            }
            try:
                with open(file_name, 'w') as f:
                    json.dump(data, f, indent=4)
                self.status_bar.showMessage(f"Project saved to {file_name}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save project: {e}")

    def import_media(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Import Media", "", "Media Files (*.png *.jpg *.jpeg *.mp4 *.mov *.avi *.mkv)")
        if file_name:
            print(f"Importing {file_name}")
            try:
                item = MediaItem(file_name)
                self.canvas.add_layer(item)
                self.layer_panel.layer_list.addItem(item.name)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load media: {e}")

    def add_quad_surface(self):
        # Create an empty surface (layer with placeholder media)
        try:
            placeholder_media = MediaItem(None) # None path triggers placeholder creation
            layer = Layer(placeholder_media)
            layer.name = f"Surface {len(self.canvas.layers) + 1}"
            
            # Add to canvas
            self.canvas.add_layer(layer)
            self.update_layer_panel()
            
            # Select the new layer (single selection)
            # Find the item in the tree and select it
            # For simplicity, just rebuild tree and select last? 
            # Or iterate to find it.
            
            self.status_bar.showMessage("New Surface Added")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create surface: {e}")

    def update_layer_panel(self):
        self.layer_panel.update_layers(self.canvas.layers)

    def on_layer_selection_changed(self):
        items = self.layer_panel.layer_tree.selectedItems()
        if not items:
            self.canvas.selected_layer = None
            self.prop_panel.set_layer(None)
            return
            
        # Get the first selected item for Property Panel (or handle multi-select properties later)
        first_item = items[0]
        layer = first_item.data(0, Qt.ItemDataRole.UserRole)
        
        self.canvas.selected_layer = layer
        self.prop_panel.set_layer(layer)
        self.canvas.update()

    def group_selected_layers(self):
        items = self.layer_panel.layer_tree.selectedItems()
        if len(items) < 2:
            self.status_bar.showMessage("Select at least 2 layers to group.")
            return
            
        selected_layers = [item.data(0, Qt.ItemDataRole.UserRole) for item in items]
        
        # Verify they are all at the same level (roots or same parent)
        # For simplicity, we only allow grouping root layers for now, 
        # or we re-parent them.
        
        # Create Group Layer
        group_media = MediaItem(None) # Placeholder/Group media
        group_layer = Layer(group_media)
        group_layer.name = "Group " + str(len(self.canvas.layers))
        
        # Move selected layers into group
        for layer in selected_layers:
            # Remove from canvas root list if present
            if layer in self.canvas.layers:
                self.canvas.layers.remove(layer)
            # Or remove from parent
            elif layer.parent:
                layer.parent.remove_child(layer)
                
            group_layer.add_child(layer)
            
        # Add group to canvas
        self.canvas.add_layer(group_layer)
        
        self.update_layer_panel()
        self.status_bar.showMessage("Layers Grouped")

    def delete_selected_layers(self):
        items = self.layer_panel.layer_tree.selectedItems()
        if not items:
            return
            
        reply = QMessageBox.question(self, "Delete Layers", "Are you sure you want to delete selected layers?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.No:
            return

        selected_layers = [item.data(0, Qt.ItemDataRole.UserRole) for item in items]
        
        for layer in selected_layers:
            # Remove from canvas root list
            if layer in self.canvas.layers:
                self.canvas.layers.remove(layer)
            # Or remove from parent
            elif layer.parent:
                layer.parent.remove_child(layer)
        
        self.canvas.selected_layer = None
        self.prop_panel.set_layer(None)
        self.update_layer_panel()
        self.canvas.update()
        self.status_bar.showMessage("Layers Deleted")

    def on_assign_media_requested(self):
        layer = self.canvas.selected_layer
        if not layer:
            return
            
        file_name, _ = QFileDialog.getOpenFileName(self, "Assign Media", "", "Media Files (*.png *.jpg *.jpeg *.mp4 *.mov *.avi *.mkv)")
        if file_name:
            try:
                new_media = MediaItem(file_name)
                layer.set_media(new_media)
                
                # Update UI
                self.prop_panel.set_layer(layer) # Refresh panel info
                self.canvas.update()
                
                self.status_bar.showMessage(f"Media assigned to {layer.name}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to assign media: {e}")

    def toggle_output(self):
        if self.output_window:
            self.output_window.close()
            self.output_window = None
            self.status_bar.showMessage("Output Window Closed")
        else:
            # Detect screens
            screens = QGuiApplication.screens()
            if len(screens) == 0:
                return
            
            target_screen = screens[0]
            if len(screens) > 1:
                # Ask user
                screen_names = [f"{s.name()} ({s.geometry().width()}x{s.geometry().height()})" for s in screens]
                item, ok = QInputDialog.getItem(self, "Select Output Display", "Display:", screen_names, 0, False)
                if ok and item:
                    index = screen_names.index(item)
                    target_screen = screens[index]
                else:
                    return
            
            self.output_window = OutputWindow(self.canvas.layers, target_screen)
            self.output_window.show()
            self.status_bar.showMessage(f"Outputting to {target_screen.name()}")

    def toggle_snapping(self, checked):
        self.canvas.snapping_enabled = checked
        self.status_bar.showMessage(f"Snapping {'Enabled' if checked else 'Disabled'}")

    def on_layer_selected_in_panel(self, item):
        name = item.text()
        # Find layer by name (simple linear search)
        for layer in self.canvas.layers:
            if layer.name == name:
                self.canvas.selected_layer = layer
                self.canvas.update()
                
                # Update properties panel
                self.prop_panel.set_layer(layer)
                break
    
    def closeEvent(self, event):
        if self.output_window:
            self.output_window.close()
        super().closeEvent(event)
