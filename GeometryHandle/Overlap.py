import json 
import shapely
from shapely.ops import unary_union
from shapely.geometry import Polygon as ShapelyPolygon

# Open the Technology File
with open("Files/TechnologyExample.json", "r") as f:
    tech = json.load(f)

# Take the information of the colors
tech_layers = tech["layers"]

def polygon_overlap(polygon_points: list = [], ref_layer_keys: list = [], all_polygons: list = [], z_zoom: float = 1) -> list:
    """
    Split a polygon into sub-regions based on overlap with reference layers.
    
    Parameters:
        polygon_points (list): The XY points of the polygon to split.
        ref_layer_keys (list): Layer keys to check overlap against.
        all_polygons (list): The full list of all polygons in the scene.
        z_zoom (float): Z zoom factor to scale z positions.
    
    Returns:
        regions (list): Each entry is a dict:
            {
                "points": [...],        # XY points of the sub-region
                "z_bottom": float       # bottom Z for this sub-region
            }
    """
    # Build the subject polygon in Shapely
    subject = ShapelyPolygon(polygon_points)
    if not subject.is_valid:
        subject = subject.buffer(0)

    # Collect reference polygons grouped by layer key, each with its top z
    ref_shapes = [] 
    for ref_polygon in all_polygons:
        ref_key = f"{ref_polygon['layer']['layer']}/{ref_polygon['layer']['datatype']}"
        if ref_key not in ref_layer_keys:
            continue
        if ref_key not in tech_layers:
            continue

        ref_info = tech_layers[ref_key]
        z_top = (ref_info["z_position"] + ref_info["height"]) * z_zoom
        ref_shape = ShapelyPolygon(ref_polygon["points"])
        if not ref_shape.is_valid:
            ref_shape = ref_shape.buffer(0)
        ref_shapes.append((ref_shape, z_top))

    # No reference polygons found: entire polygon sits at z=0
    if not ref_shapes:
        return [{"points": polygon_points, "z_bottom": 0.0}]

    # For each point in subject, figure out which ref shapes cover it
    regions = []
    remaining = subject 

    # Sort ref shapes by z_top descending so deepest stack is resolved first
    ref_shapes_sorted = sorted(ref_shapes, key=lambda x: x[1], reverse=True)

    # Build cumulative union regions from highest to lowest
    assigned = shapely.geometry.GeometryCollection() 

    for ref_shape, z_top in ref_shapes_sorted:
        
        # The overlap between subject and this ref, not yet covered by a higher layer
        overlap = remaining.intersection(ref_shape)
        if overlap.is_empty:
            continue

        # This overlap region sits on top of z_top
        regions.append({
            "points": shapely_to_points(overlap),
            "z_bottom": z_top + 0.1
        })

        # Remove this area from remaining so it won't be double-counted
        remaining = remaining.difference(ref_shape)
        if remaining.is_empty:
            break

    # Whatever is left has no overlap: sits at z=0
    if not remaining.is_empty:
        regions.append({
            "points": shapely_to_points(remaining),
            "z_bottom": 0.0
        })

    return regions


def shapely_to_points(geom : shapely.geometry = None) -> list:
    """
    Extract XY coordinate lists from a Shapely geometry into a list of point lists.
    
    Parameters:
        geom (shapely.geometry): A Shapely geometry object to extract coordinates from.

    Returns:
        result (list): A list of point-lists, one per polygon component.
    """
    # Normalize the input into a flat list of simple Polygons
    if geom.geom_type == "Polygon":
        polygons = [geom]
    elif geom.geom_type in ("MultiPolygon", "GeometryCollection"):
        # Multi-geometry: filter out any non-Polygon components
        polygons = [g for g in geom.geoms if g.geom_type == "Polygon"]
    else:
        polygons = []

    result = []
    for poly in polygons:
        coords = list(poly.exterior.coords[:-1])
        result.append(coords)

    return result