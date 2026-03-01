import json 
import numpy as np
import pyvista as pv
import GeometryHandle.Extrusion as ext

# Open the Technology File
with open("TechnologyExample.json", "r") as f:
    tech = json.load(f)

# Take the information of the colors
tech_layers = tech["layers"]

def plot_data(polygons):
    """
    Plot the polygons data in input according to the settings.
    """
    
    # Instantiate the plotter
    plotter = pv.Plotter(window_size=(1200, 800))

    # Initialize the legend
    used_layers = {}
    
    # Check all the polygons in input
    for polygon in polygons:
  
        layer_key = f"{ polygon['layer']['layer']}/{ polygon['layer']['datatype']}"

        # If we don't have information of the layer skip it
        if layer_key not in tech_layers:
            continue
        
        # Get information of the polygon
        info = tech_layers[layer_key]
        alpha = info["alpha"]
        color = info["color"]
        height = info["height"]
        polygon_points = polygon["points"]
        tolerance = tech["tolerance"]
        tolerance_col = tech["tolerance_col"]
        z_position = info["z_position"]

        # Extrude the polygon in 3D
        bot, top, lat = ext.extrude_polygon_points(points=polygon_points, 
                                                   height=height, 
                                                   z_position=z_position,
                                                   tolerance=tolerance,
                                                   tolerance_col=tolerance_col)
        
        for face in [bot, top, lat]:
            
            # Convert points to numpy array
            points = np.array(face[0])
            triangles_indexes = face[1]

            # Prepare faces array for PyVista
            faces = []
            for triangle_idx in triangles_indexes:
                faces.extend([3, triangle_idx[0], triangle_idx[1], triangle_idx[2]])
            faces = np.array(faces)
            mesh = pv.PolyData(points, faces)

            # Add the mesh to the plotter
            plotter.add_mesh(mesh, color=color, opacity=alpha, show_edges=False)
            
        # Save the layer
        used_layers[layer_key] = info

    # Legend
    legend_entries = []
    for key, info in used_layers.items():
        name = info.get("name", key)
        legend_entries.append([name, info["color"]])

    if legend_entries:
        plotter.add_legend(legend_entries, bcolor="white")

    plotter.show()