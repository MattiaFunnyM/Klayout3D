import json
import numpy as np
import pyvista as pv
from shapely.ops import unary_union, triangulate
from shapely.geometry import Polygon

#############################
### PLOTTING INFORMATIONS ###
#############################
# Open the Technology File
with open("TechnologyExample.json", "r") as f:
    tech = json.load(f)

# Take the information of the colors
tech_layers = tech["layers"]

def merge_polygons_by_layer(polygons):
    """
    Merge all polygons that belong to the same layer.
    """
    layer_groups = {}

    for poly in polygons:
        layer = poly["layer"]
        layer_key = f"{layer['layer']}/{layer['datatype']}"

        pts = poly["points"]
        shp = Polygon(pts)

        if layer_key not in layer_groups:
            layer_groups[layer_key] = []
        layer_groups[layer_key].append(shp)

    # Merge touching polygons
    merged = {}
    for layer_key, polys in layer_groups.items():
        merged[layer_key] = unary_union(polys)

    return merged

def shapely_to_mesh(shp, bottom, height):
    """
    Transform the shapely input to a mesh.
    """
    meshes = []

    if shp.geom_type == "Polygon":
        meshes.append(extrude_polygon(list(shp.exterior.coords), bottom, height))

    elif shp.geom_type == "MultiPolygon":
        for geom in shp.geoms:
            meshes.append(extrude_polygon(list(geom.exterior.coords), bottom, height))

    return meshes


def extrude_polygon(pts, bottom, height):
    """
    Extrude the 2D polygon into a 3D mesh.
    """
    pts = np.array(pts[:-1])
    n = len(pts)

    # 3D points
    bottom_pts = np.c_[pts, np.full(n, bottom)]
    top_pts    = np.c_[pts, np.full(n, bottom + height)]

    all_pts = np.vstack([bottom_pts, top_pts])

    faces = []

    # ---- SIDE FACES (unchanged) ----
    for i in range(n):
        j = (i + 1) % n
        faces.append([
            4,
            i,
            j,
            n + j,
            n + i
        ])

    # ---- TRIANGULATED BOTTOM & TOP ----
    poly2d = Polygon(pts)
    tris = triangulate(poly2d)
    
    for tri in tris:
        if not poly2d.contains(tri.centroid):
            continue

        tri_pts = np.array(tri.exterior.coords)[:-1]

        idx = []
        for p in tri_pts:
            idx.append(np.where((pts == p).all(axis=1))[0][0])

        # bottom (CCW)
        faces.append([3, idx[0], idx[1], idx[2]])

        # top (reverse winding)
        faces.append([3, n + idx[2], n + idx[1], n + idx[0]])

    return pv.PolyData(all_pts, np.hstack(faces))


def plot_data(polygons):
    """
    Plot the polygons data in input according to the settings.
    """
    plotter = pv.Plotter(window_size=(1200, 800))
    used_layers = {}

    # Merge polygons per layer
    merged = merge_polygons_by_layer(polygons)

    for layer_key, shp in merged.items():
        if layer_key not in tech_layers:
            continue

        info = tech_layers[layer_key]
        color = info["color"]
        bottom = info["bottom"]
        height = info["height"]
        alpha = info.get("alpha", 0.6)

        # Convert merged Shapely polygon(s) to PyVista meshes
        meshes = shapely_to_mesh(shp, bottom, height)

        for mesh in meshes:
            plotter.add_mesh(mesh, color=color, opacity=alpha, show_edges=False)

        used_layers[layer_key] = info

    # Legend
    legend_entries = []
    for key, info in used_layers.items():
        name = info.get("name", key)
        legend_entries.append([name, info["color"]])

    if legend_entries:
        plotter.add_legend(legend_entries, bcolor="white")

    plotter.show()
