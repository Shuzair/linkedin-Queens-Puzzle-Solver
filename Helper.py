"""
Helper functions for puzzle operations.

print_matrix
matrix_to_string
get_grid_size

"""
"""
Helper functions for puzzle operations.
"""
from typing import List, Optional, Dict, Tuple
import re
import matplotlib.pyplot as plt
import matplotlib.patches as patches


# ============================================
# TEXT OUTPUT FUNCTIONS
# ============================================

def print_matrix(matrix: List[List[List[int]]], show_indices: bool = False) -> None:
    """
    Print matrix in a human-readable format.
    
    Args:
        matrix: 2D matrix where each cell is [color_num, state]
        show_indices: If True, show row and column numbers
    
    Example output:
        1 1 2 2
        1 3 2 3
    """
    if not matrix:
        print("Empty matrix")
        return
    
    rows = len(matrix)
    cols = len(matrix[0])
    
    # Find max width needed for alignment
    max_val = max(cell[0] for row in matrix for cell in row)
    width = len(str(max_val))
    
    # Print column headers if requested
    if show_indices:
        header = "   " + " ".join(f"{c:>{width}}" for c in range(cols))
        print(header)
        print("   " + "-" * (len(header) - 3))
    
    # Print each row
    for i, row in enumerate(matrix):
        values = [f"{cell[0]:>{width}}" for cell in row]
        if show_indices:
            print(f"{i:>2}| {' '.join(values)}")
        else:
            print(" ".join(values))


def print_matrix_state(matrix: List[List[List[int]]], show_indices: bool = False) -> None:
    """
    Print matrix with state indicators.
    
    Each cell shows: <color_number><state_letter>
        - 'o' if state is 0  (empty)
        - 'q' if state is 1  (queen)
        - 'x' if state is -1 (blocked)
    
    Example output:
        1o 1o 2q 2x
        1o 3q 2o 3x
    """
    if not matrix:
        print("Empty matrix")
        return
    
    state_map = {0: 'o', 1: 'q', -1: 'x'}
    
    rows = len(matrix)
    cols = len(matrix[0])
    
    max_val = max(cell[0] for row in matrix for cell in row)
    width = len(str(max_val)) + 1
    
    if show_indices:
        header = "   " + " ".join(f"{c:>{width}}" for c in range(cols))
        print(header)
        print("   " + "-" * (len(header) - 3))
    
    for i, row in enumerate(matrix):
        values = [f"{cell[0]}{state_map.get(cell[1], '?')}".rjust(width) for cell in row]
        if show_indices:
            print(f"{i:>2}| {' '.join(values)}")
        else:
            print(" ".join(values))


def matrix_to_string(matrix: List[List[List[int]]]) -> str:
    """Convert matrix to a string representation."""
    if not matrix:
        return "Empty matrix"
    
    max_val = max(cell[0] for row in matrix for cell in row)
    width = len(str(max_val))
    
    lines = [" ".join(f"{cell[0]:>{width}}" for cell in row) for row in matrix]
    return "\n".join(lines)


# ============================================
# UTILITY FUNCTIONS
# ============================================

def get_grid_size(matrix: List[List[List[int]]]) -> Tuple[int, int]:
    """Return (rows, cols) of the matrix."""
    if not matrix:
        return (0, 0)
    return (len(matrix), len(matrix[0]))


def get_color_count(matrix: List[List[List[int]]]) -> int:
    """Return the number of unique colors in the matrix."""
    if not matrix:
        return 0
    return len({cell[0] for row in matrix for cell in row})


# ============================================
# RENDERING FUNCTIONS
# ============================================

def _parse_rgb(color_str: str) -> Tuple[float, float, float]:
    """Parse 'rgb(r, g, b)' string to normalized (0-1) tuple for matplotlib."""
    match = re.search(r'rgb\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)', color_str)
    if match:
        return tuple(int(match.group(i)) / 255 for i in (1, 2, 3))
    return (0.5, 0.5, 0.5)


def _build_color_lookup(color_map: Dict[str, int]) -> Dict[int, Tuple[float, float, float]]:
    """Build reverse lookup: color_number -> RGB tuple. Parses all colors once."""
    return {num: _parse_rgb(color_str) for color_str, num in color_map.items()}


def _get_text_color(rgb: Tuple[float, float, float]) -> str:
    """Return 'black' or 'white' based on background brightness."""
    brightness = 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]
    return 'black' if brightness > 0.5 else 'white'


def render_puzzle(
    matrix: List[List[List[int]]],
    color_map: Dict[str, int],
    cell_size: float = 1.0,
    show_grid: bool = True,
    figsize: Optional[Tuple[int, int]] = None
) -> plt.Figure:
    """
    Render puzzle as a colored grid image.
    
    Args:
        matrix: 2D matrix where each cell is [color_num, state]
        color_map: Dictionary mapping color strings to color numbers
        cell_size: Size of each cell
        show_grid: If True, show grid lines
        figsize: Figure size (width, height). Auto-calculated if None.
    
    Returns:
        matplotlib Figure object
    """
    if not matrix or not color_map:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "Empty puzzle", ha='center', va='center')
        return fig
    
    rows, cols = len(matrix), len(matrix[0])
    color_lookup = _build_color_lookup(color_map)
    
    if figsize is None:
        figsize = (cols * cell_size, rows * cell_size)
    
    fig, ax = plt.subplots(figsize=figsize)
    
    # Draw all cells
    for i in range(rows):
        for j in range(cols):
            rgb = color_lookup.get(matrix[i][j][0], (0.5, 0.5, 0.5))
            rect = patches.Rectangle(
                (j, rows - 1 - i), 1, 1,
                linewidth=0.5 if show_grid else 0,
                edgecolor='black' if show_grid else 'none',
                facecolor=rgb
            )
            ax.add_patch(rect)
    
    ax.set_xlim(0, cols)
    ax.set_ylim(0, rows)
    ax.set_aspect('equal')
    ax.axis('off')
    plt.tight_layout()
    
    return fig


def render_puzzle_state(
    matrix: List[List[List[int]]],
    color_map: Dict[str, int],
    cell_size: float = 1.0,
    show_grid: bool = True,
    figsize: Optional[Tuple[int, int]] = None,
    font_size: Optional[int] = None
) -> plt.Figure:
    """
    Render puzzle with state indicators (Q for queen, X for blocked).
    
    Args:
        matrix: 2D matrix where each cell is [color_num, state]
                state: 0 = empty, 1 = queen (Q), -1 = blocked (X)
        color_map: Dictionary mapping color strings to color numbers
        cell_size: Size of each cell
        show_grid: If True, show grid lines
        figsize: Figure size (width, height). Auto-calculated if None.
        font_size: Font size for Q/X. Auto-calculated if None.
    
    Returns:
        matplotlib Figure object
    """
    if not matrix or not color_map:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "Empty puzzle", ha='center', va='center')
        return fig
    
    rows, cols = len(matrix), len(matrix[0])
    color_lookup = _build_color_lookup(color_map)
    state_symbols = {1: 'Q', -1: 'X'}
    
    if figsize is None:
        figsize = (cols * cell_size, rows * cell_size)
    
    if font_size is None:
        font_size = max(8, min(24, int(72 / max(rows, cols))))
    
    fig, ax = plt.subplots(figsize=figsize)
    texts = []
    
    # Draw all cells and collect text
    for i in range(rows):
        for j in range(cols):
            color_num, state = matrix[i][j]
            rgb = color_lookup.get(color_num, (0.5, 0.5, 0.5))
            y_pos = rows - 1 - i
            
            rect = patches.Rectangle(
                (j, y_pos), 1, 1,
                linewidth=0.5 if show_grid else 0,
                edgecolor='black' if show_grid else 'none',
                facecolor=rgb
            )
            ax.add_patch(rect)
            
            if state in state_symbols:
                texts.append((j + 0.5, y_pos + 0.5, state_symbols[state], _get_text_color(rgb)))
    
    # Batch add text (more efficient)
    for x, y, symbol, color in texts:
        ax.text(x, y, symbol, ha='center', va='center',
                fontsize=font_size, fontweight='bold', color=color)
    
    ax.set_xlim(0, cols)
    ax.set_ylim(0, rows)
    ax.set_aspect('equal')
    ax.axis('off')
    plt.tight_layout()
    
    return fig


def save_puzzle_image(fig: plt.Figure, filepath: str, dpi: int = 150) -> None:
    """Save puzzle figure to file and close it."""
    fig.savefig(filepath, dpi=dpi, bbox_inches='tight', pad_inches=0.1)
    plt.close(fig)