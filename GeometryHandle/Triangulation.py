import numpy as np
import matplotlib.pyplot as plt
from matplotlib.path import Path
from scipy.spatial import Delaunay
from matplotlib.collections import LineCollection

def simplify_point(points: list = [], tolerance: float = 0.0, max_distance: float = None) -> list:
    """
    Simplifies the points list in input such that two consecutive points
    have a distance in both x and y direction greater than the tolerance.
    Densifies the result by inserting midpoints between consecutive
    points that are farther apart than max_distance.

    Parameters:
        points (list): ordered list of (x, y) coordinates representing the vertices of a closed polygon.
        tolerance (float): minimum x or y distance between consecutive points to consider them distinct.
        max_distance (float): maximum allowed distance between two consecutive points.
                              If None, no densification is performed.
    """
    # 0. Preliminary checks
    if tolerance < 0:
        raise ValueError("Tolerance must be non-negative.")

    # If there are less than 3 points we cannot simplify it.
    if len(points) < 3:
        return points

    # Convert to numpy array for consistent arithmetic across all operations
    pts = np.array(points)

    # 1. Simplification: remove points that are too close to the previous kept point
    simplified = [pts[0]]
    for i in range(1, len(pts)):
        dist = np.max(np.abs(pts[i] - simplified[-1]))
        if dist >= tolerance:
            simplified.append(pts[i])

    # 2. Densification: insert midpoints between consecutive points that are too far apart
    if max_distance is not None:
        densified = [simplified[0]]
        for i in range(1, len(simplified)):
            prev_pt = simplified[i - 1]
            curr_pt = simplified[i]

            # Compute the Euclidean distance between the two consecutive points
            segment_length = np.linalg.norm(curr_pt - prev_pt)

            if segment_length > max_distance:
                # Number of segments needed to respect max_distance
                n_splits = int(np.ceil(segment_length / max_distance))
                for k in range(1, n_splits):
                    intermediate_pt = prev_pt + k / n_splits * (curr_pt - prev_pt)
                    densified.append(intermediate_pt)

            densified.append(curr_pt)
        return densified

    return simplified

def triangulate_polygon(points: list = [], tolerance: float = 0.0, max_distance: float = None) -> tuple[list, list]:
    """
    Generate a list of array with 3 elements, each corresponding to a vertex of the triangle.
    
    Parameters:
        points (list): ordered list of (x, y) coordinates representing the vertices of a closed polygon.
            The polygon can be concave and can contain holes. 
        tolerance (float): minimum tolerance between points to consider distinct.
        max_distance (float): maximum allowed distance between two consecutive points.
                        If None, no densification is performed.
    
    Returns:
            points (list): Simplified list of points after applying the tolerance.
            triangle_points (list): Array of triangles indexes. Each element is formed by 3 integers.
    """
    # 0. Preliminary checks
    if len(points) < 3:
        raise ValueError("At least 3 points are required to form a polygon.")
    
    # 1. Simplify data
    points = simplify_point(points = points, 
                            tolerance = tolerance,
                            max_distance = max_distance)
    
    # 2. Take only x and y coordinates if more are provided
    points_2D = np.array(points)[:, :2]

    # 3. Use Delaunay triangulation method
    triangle_indexes = Delaunay(points_2D).simplices

    # 4. Remove triangles outside the concave boundary
    centroids = np.mean(points_2D[triangle_indexes], axis=1)
    polygon_path = Path(points_2D)
    inside_mask = polygon_path.contains_points(centroids)
    triangle_indexes = triangle_indexes[inside_mask].tolist()

    return points, triangle_indexes


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
    tolerance = 0.01
    tolerance_col = 0.001
    square_points, square_indexes = triangulate_polygon(points=square_points, 
                                                        tolerance=tolerance,
                                                        tolerance_col=tolerance_col)
    circle_points, circle_indexes = triangulate_polygon(points=circle_points, 
                                                        tolerance=tolerance,
                                                        tolerance_col=tolerance_col)
    letter_c_points, letter_c_indexes = triangulate_polygon(points=letter_c_points, 
                                                            tolerance=tolerance,
                                                            tolerance_col=tolerance_col)
    letter_o_points, letter_o_indexes = triangulate_polygon(points=letter_o_points, 
                                                            tolerance=tolerance,
                                                            tolerance_col=tolerance_col)
    
    # ==========================================
    # PLOTTING
    # ==========================================
    # Set up plotting
    fig, axs = plt.subplots(2, 2, figsize=(10, 10))
    fig.suptitle('Polygon Triangulation', fontsize=16)
    
    def plot_triangulation(ax, points, triangles, title, cmap_name='plasma'):
        points = np.asarray(points)
        triangles = np.asarray(triangles)
        n_points = len(points)
        
        # 1. Initialize Colormap
        cmap = plt.get_cmap(cmap_name)

        # 2. Extract unique edges and calculate their average index
        edge_map = {}
        for tri in triangles:
            for i in range(3):
                p1_idx, p2_idx = tri[i], tri[(i+1)%3]
                
                # Key is sorted tuple to treat (1,0) and (0,1) as the same edge
                edge_key = tuple(sorted((p1_idx, p2_idx)))
                if edge_key not in edge_map:
                    
                    # Store the average position in the sequence
                    edge_map[edge_key] = (p1_idx + p2_idx) / 2.0

        # 3. Create LineCollection for efficiency
        lines = []
        colors = []
        for (p1_idx, p2_idx), avg_idx in edge_map.items():
            lines.append([points[p1_idx], points[p2_idx]])
            
            # Normalize the index to [0.0, 1.0] for the colormap
            colors.append(cmap(avg_idx / (n_points - 1)))

        line_coll = LineCollection(lines, colors=colors, linewidths=1.2, alpha=0.8)
        ax.add_collection(line_coll)

        # 4. Plot points with the same gradient
        point_colors = cmap(np.linspace(0, 1, n_points))
        ax.scatter(points[:, 0], points[:, 1], c=point_colors, s=25, 
                zorder=3, edgecolors='black', linewidths=0.3)

        # 5. UI Formatting
        ax.set_title(title)
        ax.set_aspect('equal')
        if n_points > 0:
            ax.set_xlim(points[:, 0].min() - 0.1, points[:, 0].max() + 0.1)
            ax.set_ylim(points[:, 1].min() - 0.1, points[:, 1].max() + 0.1)
        ax.axis('off')
     

    # Process & Plot Square
    plot_triangulation(axs[0, 0], square_points, square_indexes, 'Square')
    
    # Process & Plot Circle
    plot_triangulation(axs[0, 1], circle_points, circle_indexes, 'Circle')
    
    # Process & Plot Letter C
    plot_triangulation(axs[1, 0], letter_c_points, letter_c_indexes, 'Letter C')
    
    # Process & Plot Letter O (Hole)
    plot_triangulation(axs[1, 1], letter_o_points, letter_o_indexes, 'Letter O')
    
    plt.tight_layout()
    plt.show()