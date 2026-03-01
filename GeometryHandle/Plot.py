import sys
import json 
import trimesh
import numpy as np
import pyvista as pv
import GeometryHandle.Overlap as ovp
import GeometryHandle.Extrusion as ext

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from pyvistaqt import QtInteractor
from PyQt5.QtWidgets import (
    QApplication, 
    QMainWindow, 
    QVBoxLayout, 
    QHBoxLayout, 
    QPushButton, 
    QFileDialog,
    QWidget,
    QSlider, 
    QLabel, 
    QFrame
)

# Open the Technology File
with open("Files/TechnologyExample.json", "r") as f:
    tech = json.load(f)

# Take the information of the colors
tech_layers = tech["layers"]

def polygons_extrusion_zoomed(actors: list = [], plotter: pv.plotter = None, polygons: list = [], z_zoom: float = 1.0):
    """
    Extrude the polygons based on the zoom and create a 3D scene with PyVista. 

    Parameters:
        actors (list): List of PyVista actors to update with the new meshes. If empty, new actors will be created.
        plotter (pv.plotter): The PyVista plotter instance to use for rendering.
        polygons (list): A list of polygon data structures.
        z_zoom (float): The zoom factor for the Z-axis.

    Returns:
        actors (list): A list of PyVista actors that were created or updated.
    """

    # Clear the previous plotter content
    no_actors = len(actors) == 0
    actor_idx = 0

    # Loop all the polygons
    for polygon in polygons:
        
        # Understand if the layer is known
        layer_key = f"{polygon['layer']['layer']}/{polygon['layer']['datatype']}"
        if layer_key not in tech_layers:
            continue
        
        # Get information from the technology file
        info = tech_layers[layer_key]
        alpha = info["alpha"]
        color = info["color"]
        polygon_points = polygon["points"]
        tolerance = tech["tolerance"]
        max_distance = tech["max_distance"]
        height = info["height"] * z_zoom
        z_position = info["z_position"] 

        # Resolve z_position 
        if isinstance(z_position, list):
            #  If it's a list we need to differentiate differnt sub_regions
            sub_regions = ovp.polygon_overlap(
                polygon_points=polygon_points,
                ref_layer_keys=z_position,
                all_polygons=polygons,
                z_zoom=z_zoom
            )
        else:
            # If it's a float we can just assigne the z_bottom value
            sub_regions = [{"points": [polygon_points], "z_bottom": z_position * z_zoom}]

        for region in sub_regions:
            for region_points in region["points"]:
                z_position = region["z_bottom"]

                bot, top, lat = ext.extrude_polygon_points(
                    points=region_points,
                    height=height,
                    z_position=z_position,
                    tolerance=tolerance,
                    max_distance=max_distance
                )

                for face in [bot, top, lat]:
                    points = np.array(face[0])
                    triangles_indexes = face[1]
                    faces = []
                    for triangle_idx in triangles_indexes:
                        faces.extend([3, triangle_idx[0], triangle_idx[1], triangle_idx[2]])
                    faces = np.array(faces)

                    mesh = pv.PolyData(points, faces)

                    if no_actors:
                        actor = plotter.add_mesh(mesh, color=color, opacity=alpha, show_edges=False)
                        actors.append(actor)
                    else:
                        actors[actor_idx].GetMapper().SetInputData(mesh)
                        actor_idx += 1

    return actors

def plot_data(polygons: list = []):
    """
    Create a 3D plot of the polygons taken in input.

    Parameters:
        polygons (list): A list of polygon data structures.
    """
    ####################
    # PLOT WINDOW PART #
    ####################

    app = QApplication.instance() or QApplication(sys.argv)

    # Initialization of the Main Window
    window = QMainWindow()
    window.setWindowTitle("3D Layer Viewer")
    window.resize(1200, 700)
    window.setStyleSheet("background-color: #1e1e2e;")

    central_widget = QWidget()
    window.setCentralWidget(central_widget)
    main_layout = QVBoxLayout(central_widget)
    main_layout.setContentsMargins(10, 10, 10, 10)
    main_layout.setSpacing(8)

    # Initialization of the PyVista Qt Interactor
    plotter = QtInteractor(central_widget)
    plotter.set_background("#1e1e2e")
    main_layout.addWidget(plotter.interactor, stretch=1)

    # Creation of the Slider Panel
    panel = QFrame()
    panel.setStyleSheet("""
        QFrame {
            background-color: #2a2a3e;
            border-radius: 10px;
            padding: 4px;
        }
    """)
    panel_layout = QHBoxLayout(panel)
    panel_layout.setContentsMargins(16, 8, 16, 8)

    # Label of the panel
    title_label = QLabel("Z Multiplier")
    title_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
    title_label.setStyleSheet("color: #cdd6f4;")
    panel_layout.addWidget(title_label)

    # Slider
    slider = QSlider(Qt.Horizontal)
    slider.setMinimum(25)
    slider.setMaximum(1000)
    slider.setValue(100)
    slider.setTickInterval(25)
    slider.setTickPosition(QSlider.TicksBelow)
    slider.setStyleSheet("""
        QSlider::groove:horizontal {
            height: 6px;
            background: #45475a;
            border-radius: 3px;
        }
        QSlider::handle:horizontal {
            background: #89b4fa;
            border: 2px solid #1e1e2e;
            width: 18px;
            height: 18px;
            margin: -7px 0;
            border-radius: 9px;
        }
        QSlider::sub-page:horizontal {
            background: #89b4fa;
            border-radius: 3px;
        }
    """)
    panel_layout.addWidget(slider, stretch=1)

    # Value display
    value_label = QLabel("1.00×")
    value_label.setFont(QFont("Segoe UI", 10))
    value_label.setStyleSheet("color: #89b4fa; min-width: 48px;")
    value_label.setAlignment(Qt.AlignCenter)
    panel_layout.addWidget(value_label)

    # Save button
    save_button = QPushButton("⬇ Export PLY")
    save_button.setFont(QFont("Segoe UI", 10))
    save_button.setStyleSheet("""
        QPushButton {
            background-color: #313244;
            color: #cdd6f4;
            border: 1px solid #45475a;
            border-radius: 6px;
            padding: 4px 14px;
        }
        QPushButton:hover {
            background-color: #45475a;
        }
        QPushButton:pressed {
            background-color: #89b4fa;
            color: #1e1e2e;
        }
    """)
    panel_layout.addWidget(save_button)
    main_layout.addWidget(panel)

    ########################
    # DRAW POLYGONS PART   #
    ########################
    actors = []

    def on_slider_change(raw_value):
        nonlocal actors
        z_zoom = raw_value / 100.0
        value_label.setText(f"{z_zoom:.2f}×")
        actors = polygons_extrusion_zoomed(
            actors=actors,
            plotter=plotter,
            polygons=polygons,
            z_zoom=z_zoom
        )
        plotter.render()

    def on_save():
        """
        Open a file dialog and export the current 3D scene as a PLY file.
        PLY is natively supported by Blender via File -> Import -> PLY.
        All meshes are merged into a single PLY file.
        """
        file_path, _ = QFileDialog.getSaveFileName(
            window,
            "Export 3D Scene",
            "scene.ply",
            "Stanford PLY (*.ply);;All Files (*)"
        )
        if not file_path:
            return

        # Merge all actor meshes into a single PolyData and save as PLY
        combined = pv.PolyData()
        for actor in actors:
            mesh = actor.GetMapper().GetInput()
            if mesh is not None:
                combined = combined.merge(pv.wrap(mesh))
        combined.save(file_path)

    slider.valueChanged.connect(on_slider_change)
    save_button.clicked.connect(on_save)

    # Initial render
    on_slider_change(100)

    window.show()
    app.exec_()