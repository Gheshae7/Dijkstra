"""
graph.py  -  تبدیل ماز به گراف: هر خانه‌ی آزاد یک گره است و راه بین خانه‌های کناری هم یک یال.
گراف فقط یک بار برای هر ماز ساخته می‌شود و Dijkstra از آن استفاده می‌کند.
"""

from settings import DIRECTIONS, STEP_COST, WALL


def get_neighbors(grid, cell):
    """همسایه‌های آزاد یک خانه را در چهار جهت پیدا می‌کند."""

    row, col = cell
    neighbors = []

    for dr, dc in DIRECTIONS:
        nr, nc = row + dr, col + dc

        # بررسی می‌کنیم خانه داخل محدوده ماز باشد.
        inside = 0 <= nr < len(grid) and 0 <= nc < len(grid[0])

        # فقط خانه‌های آزاد می‌توانند همسایه باشند.
        if inside and grid[nr][nc] != WALL:
            neighbors.append((nr, nc))

    return neighbors


def build_graph(grid):
    """گراف ماز را از خانه‌های آزاد و همسایه‌های آن‌ها می‌سازد."""

    graph = {}

    for row in range(len(grid)):
        for col in range(len(grid[0])):

            if grid[row][col] != WALL:
                cell = (row, col)

                # هر همسایه همراه با هزینه حرکت ذخیره می‌شود.
                graph[cell] = [
                    (neighbor, STEP_COST)
                    for neighbor in get_neighbors(grid, cell)
                ]

    return graph
