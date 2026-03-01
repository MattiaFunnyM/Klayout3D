import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

try:
    import GeometryHandle.Triangulation as tri
except ModuleNotFoundError:
    import Triangulation as tri

def extrude_polygon_points(points: list = [], height: float = 0.0, z_position: float = 0.0, tolerance: float = 0.01, max_distance: float = None):
    """
    Generate 3 list of array representing the vertices of the bottom, top and lateral surface.
    
    Parameters:
        points (list): ordered list of (x, y) coordinates representing the vertices of a closed polygon.
            The polygon can be concave. Assume the points list is simplified.
        height (float): extrusion height along the z-axis.
        z_position (float): starting z coordinate of the extrusion.
        tolerance (float): minimum x or y distance between consecutive points to consider them distinct.
        max_distance (float): maximum allowed distance between two consecutive points.
                              If None, no densification is performed.

    Returns:
        bottom_points (list): List of (x, y, z) points at z_position.
        top_points (list): List of (x, y, z) points at z_position + height.
        lateral_points (list): List of (x, y, z) points for the lateral surface.
    """

    # 0. Preliminary checks
    if len(points) < 3:
        raise ValueError("At least 3 points are required to form a polygon.")

    # 1. Generate bottom surface
    bottom_points = [[x, y, z_position] for (x, y) in points]
    bottom_points, bottom_triangle_indexes = tri.triangulate_polygon(points=bottom_points, 
                                                                     tolerance=tolerance,
                                                                     max_distance=max_distance)
    bottom = [bottom_points, bottom_triangle_indexes]
    
    # 2. Generate top surface
    top_points = [[x, y, z + height] for (x, y, z) in bottom_points]
    top_triangle_indexes = bottom_triangle_indexes
    top = [top_points, top_triangle_indexes]

    # 3. Generate lateral 
    lateral_points = bottom_points + [bottom_points[0]] + top_points + [top_points[0]]
    lateral_triangle_indexes = []
    half = len(bottom_points) + 1
 
    for idx in range(half - 1):
        # Bottom loop indices
        b_i      = idx
        b_next   = idx + 1

        # Top loop indices (offset by half)
        t_i      = half + idx
        t_next   = half + idx + 1

        # Triangle 1
        lateral_triangle_indexes.append([b_i, b_next, t_i])

        # Triangle 2
        lateral_triangle_indexes.append([b_next, t_next, t_i])

    lateral = [lateral_points, lateral_triangle_indexes]

    return bottom, top, lateral


if __name__ == '__main__':
    # ==========================================
    # 1. SQUARE
    # ==========================================
    square_points = ([[0, 0], [1, 0], [1, 1], [0, 1]])
    
    # ==========================================
    # 2. CIRCLE
    # ==========================================
    # We intentionally add a lot of points to test the simplification
    t = np.linspace(0, 2 * np.pi, 200, endpoint=False)
    circle_points = np.column_stack([np.cos(t), np.sin(t)]).tolist()
    
    # ==========================================
    # 3. LETTER 'C' (Concave Loop)
    # ==========================================
    # Outer arc
    t_c_out = np.linspace(np.pi/4, 7*np.pi/4, 30)
    outer_c = np.column_stack([np.cos(t_c_out), np.sin(t_c_out)])
    
    # Inner arc
    t_c_in = np.linspace(7*np.pi/4, np.pi/4, 30)
    inner_c = np.column_stack([0.6 * np.cos(t_c_in), 0.6 * np.sin(t_c_in)])
    
    # Combine
    letter_c_points = np.vstack([outer_c, inner_c]).tolist()
    
    # ==========================================
    # 4. LETTER 'O' (Loop containing a Loop)
    # ==========================================
    t_o = np.linspace(0, 2 * np.pi, 50, endpoint=False)
    outer = np.column_stack([np.cos(t_o), np.sin(t_o)])
    inner = np.column_stack([0.5 * np.cos(t_o[::-1]), 0.5 * np.sin(t_o[::-1])])
    letter_o_points = np.vstack([outer, outer[0], inner, inner[0]]).tolist()
      
    # ==========================================
    # TESTING
    # ==========================================
    height = 5
    z_position = 0
    tol = 0.01
    tol_col = 0.001
    
    output_points_array = []
    output_triangle_array = []
    output_kind_array = []

    # Test all points drawn
    for idp, points in enumerate([square_points, circle_points, letter_c_points, letter_o_points]):
        
        # By extruding the 2D shape
        extruded_points_list = extrude_polygon_points(points=points, 
                                                      height=height, 
                                                      z_position=z_position,
                                                      tolerance=tol,
                                                      tolerance_col=tol_col)
        for idx in range(3):
            output_points_array.append(extruded_points_list[idx][0])
            output_triangle_array.append(extruded_points_list[idx][1])
            output_kind_array.append(idp)
    
    # ==========================================
    # PLOTTING
    # ==========================================
    # Set up plotting
    fig = plt.figure(figsize=(8, 8))
    fig.suptitle('Polygon Triangulation', fontsize=16)

    # Create 4 subplots with 3D projection
    axs = [
        fig.add_subplot(2, 2, 1, projection='3d'),
        fig.add_subplot(2, 2, 2, projection='3d'),
        fig.add_subplot(2, 2, 3, projection='3d'),
        fig.add_subplot(2, 2, 4, projection='3d'),
    ]

    def plot_3d_points(ax, points, triangles, title, cmap_name='plasma'):

        # 1. Initialize Colormap amd axes
        ax.set_title(title)
        cmap = plt.get_cmap(cmap_name)
        colors = np.linspace(0, 1, len(points))

        # 2. Extract x, y, z coordinates and assign colors based on index
        xs = np.array([p[0] for p in points])
        ys = np.array([p[1] for p in points])
        zs = np.array([p[2] for p in points])
        triangles = np.asarray(triangles)
   
        # 3. Create the 3D scatter plot for points
        ax.scatter(xs, ys, zs, c=colors, cmap=cmap_name)
        
        # 4. Draw triangles using triangle indexes
        triangle_vertices = np.array([[
            [xs[tri[0]], ys[tri[0]], zs[tri[0]]],
            [xs[tri[1]], ys[tri[1]], zs[tri[1]]],
            [xs[tri[2]], ys[tri[2]], zs[tri[2]]],
        ] for tri in triangles])

        # 5. Assign a color to each triangle based on its mean index
        triangle_colors = cmap(np.array([
            np.mean(tri) / len(points)
            for tri in triangles
        ]))

        # 6. Create and add the triangle collection
        mesh = Poly3DCollection(
            triangle_vertices,
            facecolors=triangle_colors,
            edgecolors='black',       
            linewidths=0.5,
            alpha=0.9
        )
        ax.add_collection3d(mesh)
  
     
    # Process & Plot Square
    for idp, kind in enumerate(output_kind_array):
        title = ['Square', 'Circle', 'Letter C', 'Letter O'][kind]
        plot_3d_points(ax=axs[kind], 
                       points=output_points_array[idp], 
                       triangles=output_triangle_array[idp], 
                       title=title)

    
    plt.tight_layout()
    plt.show()