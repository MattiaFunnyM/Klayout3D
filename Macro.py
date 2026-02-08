# This is the script for the macro that you have to run from Klayout part
import pya
import socket
import json

# ------------------------------------------------------------
# Send data to external Python plotter
# ------------------------------------------------------------
def send_to_plotter(payload_dict):
    try:
        payload = json.dumps(payload_dict).encode()

        # Prefix with 4‑byte length
        msg = len(payload).to_bytes(4, "big") + payload

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("127.0.0.1", 50007))
        s.sendall(msg)
        s.close()

        pya.Logger.info("Data sent to external plotter.")
    except Exception as e:
        pya.Logger.error(f"Failed to send data: {e}")


# ------------------------------------------------------------
# Collect ruler region (user-drawn box)
# ------------------------------------------------------------
def get_ruler_region_in_dbu(view, layout):
    region = pya.Region()
    dbu = layout.dbu  # microns per DBU

    for ann in view.each_annotation():
        try:
            dbox = ann.box()  # pya.DBox in microns
        except Exception:
            dbox = None

        if dbox is not None and not dbox.empty():
            box = pya.Box(
                int(dbox.left / dbu),
                int(dbox.bottom / dbu),
                int(dbox.right / dbu),
                int(dbox.top / dbu)
            )
            region.insert(box)

    return region


# ------------------------------------------------------------
# Main logic
# ------------------------------------------------------------
def main():
    view = pya.LayoutView.current()
    if view is None:
        pya.Logger.info("No layout open.")
        return

    cellview = view.active_cellview()
    if cellview is None:
        pya.Logger.info("No active cell view.")
        return

    layout = cellview.layout()
    top_cell = cellview.cell
    if top_cell is None:
        pya.Logger.info("No top cell found.")
        return

    dbu = layout.dbu

    # Get ruler box region
    selection_region = get_ruler_region_in_dbu(view, layout)
    if selection_region.is_empty():
        pya.Logger.info("No ruler box found.")
        return

    bbox_dbu = selection_region.bbox()
    bbox_micron = pya.DBox(bbox_dbu) * dbu
    pya.Logger.info(f"Selection box (microns): {bbox_micron}")

    all_polygons = []

    # Iterate through all layers
    for layer_index in layout.layer_indexes():
        layer_info = layout.get_info(layer_index)

        it = top_cell.begin_shapes_rec_overlapping(layer_index, bbox_dbu)

        while not it.at_end():
            shape = it.shape()
            trans = it.trans()

            shape_region_local = pya.Region()

            if shape.is_box():
                shape_region_local.insert(shape.box)
            elif shape.is_polygon():
                shape_region_local.insert(shape.polygon)
            else:
                it.next()
                continue

            # Transform to top-level coordinates
            shape_region_top = shape_region_local.transformed(trans)

            # Intersect with ruler region
            shape_intersection = shape_region_top & selection_region

            if not shape_intersection.is_empty():
              for poly in shape_intersection.each():
                pts = []
            
                # Convert Region polygon → SimplePolygon
                polygon = poly.to_simple_polygon()
            
                for p in polygon.each_point():
                    pts.append([p.x * dbu, p.y * dbu])
            
                all_polygons.append({
                    "layer": {
                        "layer": layer_info.layer,
                        "datatype": layer_info.datatype
                    },
                    "points": pts
                })

            it.next()

    # Send to external plotter
    if all_polygons:
        send_to_plotter({"polygons": all_polygons})
    else:
        pya.Logger.info("No polygons found in selection.")


# ------------------------------------------------------------
# Run
# ------------------------------------------------------------
if __name__ == "__main__":
    main()
