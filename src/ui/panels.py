from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QListWidget, 
                             QPushButton, QSlider, QGroupBox, QFormLayout, 
                             QScrollArea, QHBoxLayout, QSpinBox, QComboBox,
                             QTreeWidget, QTreeWidgetItem, QAbstractItemView,
                             QCheckBox)
from PyQt6.QtCore import Qt, pyqtSignal

class LayerPanel(QWidget):
    # Signals for actions
    deleteRequested = pyqtSignal()
    groupRequested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("Layers"))
        
        # Use QTreeWidget instead of QListWidget for hierarchy
        self.layer_tree = QTreeWidget()
        self.layer_tree.setHeaderHidden(True)
        self.layer_tree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        layout.addWidget(self.layer_tree)
        
        controls = QHBoxLayout()
        
        # Group Button
        self.group_btn = QPushButton("Group")
        self.group_btn.clicked.connect(self.groupRequested.emit)
        controls.addWidget(self.group_btn)
        
        # Delete Button
        self.del_btn = QPushButton("Delete")
        self.del_btn.clicked.connect(self.deleteRequested.emit)
        controls.addWidget(self.del_btn)
        
        layout.addLayout(controls)

    def update_layers(self, layers):
        """Rebuilds the layer tree from the list of root layers."""
        self.layer_tree.clear()
        
        for layer in layers:
            self._add_layer_item(layer, self.layer_tree)

    def _add_layer_item(self, layer, parent_item):
        item = QTreeWidgetItem(parent_item)
        item.setText(0, layer.name)
        # Store reference to layer object if needed, or just rely on index/name?
        # Storing object in data is safer
        item.setData(0, Qt.ItemDataRole.UserRole, layer)
        
        for child in layer.children:
            self._add_layer_item(child, item)
            
        item.setExpanded(True)

class PropertyPanel(QWidget):
    layerChanged = pyqtSignal()
    assignMediaRequested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_layer = None
        layout = QVBoxLayout(self)
        
        # --- Media Info & Assignment ---
        media_group = QGroupBox("Media Source")
        media_layout = QVBoxLayout()
        
        self.media_name_label = QLabel("No Media")
        media_layout.addWidget(self.media_name_label)
        
        self.assign_media_btn = QPushButton("Assign/Change Media")
        self.assign_media_btn.clicked.connect(self.on_assign_media)
        media_layout.addWidget(self.assign_media_btn)
        
        # Group Options (Span Media)
        self.span_media_chk = QCheckBox("Span Media Across Children")
        self.span_media_chk.toggled.connect(self.on_span_changed)
        self.span_media_chk.setVisible(False)
        media_layout.addWidget(self.span_media_chk)
        
        media_group.setLayout(media_layout)
        layout.addWidget(media_group)
        
        # Mapping Properties
        mapping_group = QGroupBox("Mapping")
        mapping_layout = QFormLayout()
        
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(100)
        self.opacity_slider.valueChanged.connect(self.on_opacity_changed)
        mapping_layout.addRow("Opacity", self.opacity_slider)
        
        # Blend Mode
        self.blend_combo = QComboBox()
        self.blend_combo.addItems(["Normal", "Add", "Multiply", "Screen"])
        self.blend_combo.currentTextChanged.connect(self.on_blend_changed)
        mapping_layout.addRow("Blend Mode", self.blend_combo)
        
        # Grid Warp
        grid_layout = QHBoxLayout()
        self.rows_spin = QSpinBox()
        self.rows_spin.setRange(2, 20)
        self.rows_spin.setValue(2)
        self.rows_spin.valueChanged.connect(self.on_grid_changed)
        
        self.cols_spin = QSpinBox()
        self.cols_spin.setRange(2, 20)
        self.cols_spin.setValue(2)
        self.cols_spin.valueChanged.connect(self.on_grid_changed)
        
        grid_layout.addWidget(QLabel("Rows:"))
        grid_layout.addWidget(self.rows_spin)
        grid_layout.addWidget(QLabel("Cols:"))
        grid_layout.addWidget(self.cols_spin)
        mapping_layout.addRow("Grid Size", grid_layout)
        
        mapping_group.setLayout(mapping_layout)
        layout.addWidget(mapping_group)
        
        # Masking
        mask_group = QGroupBox("Masking")
        mask_layout = QVBoxLayout()
        
        self.add_mask_btn = QPushButton("Add Rect Mask")
        self.add_mask_btn.clicked.connect(self.on_add_mask)
        mask_layout.addWidget(self.add_mask_btn)
        
        self.clear_masks_btn = QPushButton("Clear Masks")
        self.clear_masks_btn.clicked.connect(self.on_clear_masks)
        mask_layout.addWidget(self.clear_masks_btn)
        
        mask_group.setLayout(mask_layout)
        layout.addWidget(mask_group)
        
        # Color Correction
        color_group = QGroupBox("Color Correction")
        color_layout = QFormLayout()
        color_layout.addRow("Brightness", QSlider(Qt.Orientation.Horizontal))
        color_layout.addRow("Contrast", QSlider(Qt.Orientation.Horizontal))
        color_group.setLayout(color_layout)
        layout.addWidget(color_group)
        
        layout.addStretch()
        
        self.setEnabled(False) # Disabled until layer selected

    def on_assign_media(self):
        self.assignMediaRequested.emit()

    def on_span_changed(self, checked):
        if self.current_layer:
            self.current_layer.span_group_media = checked
            self.layerChanged.emit()

    def set_layer(self, layer):
        self.current_layer = layer
        if layer:
            self.setEnabled(True)
            name = layer.media.name if layer.media else "No Media"
            self.media_name_label.setText(f"Source: {name}")
            
            self.opacity_slider.blockSignals(True)
            self.opacity_slider.setValue(int(layer.opacity * 100))
            self.opacity_slider.blockSignals(False)
            
            self.blend_combo.blockSignals(True)
            self.blend_combo.setCurrentText(layer.blend_mode)
            self.blend_combo.blockSignals(False)
            
            self.rows_spin.blockSignals(True)
            self.rows_spin.setValue(layer.grid_rows)
            self.rows_spin.blockSignals(False)
            
            self.cols_spin.blockSignals(True)
            self.cols_spin.setValue(layer.grid_cols)
            self.cols_spin.blockSignals(False)
            
            # Show/Hide Span Checkbox if group
            self.span_media_chk.blockSignals(True)
            if layer.children:
                self.span_media_chk.setVisible(True)
                self.span_media_chk.setChecked(layer.span_group_media)
            else:
                self.span_media_chk.setVisible(False)
            self.span_media_chk.blockSignals(False)

        else:
            self.media_name_label.setText("No Selection")
            self.setEnabled(False)

    def on_opacity_changed(self, value):
        if self.current_layer:
            self.current_layer.opacity = value / 100.0
            self.layerChanged.emit()
            
    def on_blend_changed(self, text):
        if self.current_layer:
            self.current_layer.blend_mode = text
            self.layerChanged.emit()

    def on_grid_changed(self):
        if self.current_layer:
            rows = self.rows_spin.value()
            cols = self.cols_spin.value()
            self.current_layer.set_grid_size(rows, cols)
            self.layerChanged.emit()

    def on_add_mask(self):
        if self.current_layer:
            # Default to top-left of mesh + offset
            p0 = self.current_layer.mesh_points[0, 0]
            cx, cy = p0[0] + 50, p0[1] + 50
            
            mask = [
                [cx, cy],
                [cx + 100, cy],
                [cx + 100, cy + 100],
                [cx, cy + 100]
            ]
            self.current_layer.masks.append(mask)
            self.layerChanged.emit()

    def on_clear_masks(self):
        if self.current_layer:
            self.current_layer.masks = []
            self.layerChanged.emit()

    def on_assign_media(self):
        self.assignMediaRequested.emit()

class TimelinePanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        
        controls = QHBoxLayout()
        controls.addWidget(QPushButton("Play"))
        controls.addWidget(QPushButton("Stop"))
        controls.addWidget(QSlider(Qt.Orientation.Horizontal))
        
        layout.addLayout(controls)
