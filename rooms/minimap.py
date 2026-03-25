from __future__ import annotations

import pygame

from rooms.floor_map import FloorMap, RoomNode, DIRECTIONS


# ---- Layout ----
MINIMAP_MARGIN   = 16     # px from screen edge
MINIMAP_PADDING  = 10     # px inside the panel border
ROOM_SIZE        = 16     # px per room square
ROOM_GAP         = 6      # px between rooms (door corridors live here)
DOOR_THICKNESS   = 3      # px wide door line
CELL             = ROOM_SIZE + ROOM_GAP   # total grid cell pitch

# ---- Colors ----
_C = {
    "panel_bg":    (12,  12,  18,  180),
    "panel_border":(60,  60,  80),

    "current":     (255, 255, 255),
    "combat":      (100, 100, 120),
    "start":       (80,  200, 120),
    "boss":        (220, 55,  55),
    "elite":       (255, 180, 40),
    "reward":      (80,  180, 255),

    "door":        (160, 160, 170),
    "door_to_unknown": (80, 80, 90),
}

def _room_color(node: RoomNode, is_current: bool) -> tuple:
    if is_current:
        return _C["current"]
    return _C.get(node.room_type, _C["combat"])


class Minimap:
    """
    Draws a small map of visited rooms in the corner of the screen.

    Usage
    -----
    minimap = Minimap()

    # In PlayingState.draw():
    minimap.draw(screen, room_manager.floor_map, room_manager.current_node)
    """

    def __init__(self):
        self._font = None

    def draw(
        self,
        screen: pygame.Surface,
        floor_map: FloorMap | None,
        current_node: RoomNode | None,
    ):
        if floor_map is None or current_node is None:
            return

        visited = {
            pos: node for pos, node in floor_map.nodes.items()
            if node.visited
        }
        if not visited:
            return

        # --- Compute bounding box of visited rooms ---
        all_gx = [pos[0] for pos in visited]
        all_gy = [pos[1] for pos in visited]
        min_gx, max_gx = min(all_gx), max(all_gx)
        min_gy, max_gy = min(all_gy), max(all_gy)

        cols = max_gx - min_gx + 1
        rows = max_gy - min_gy + 1

        content_w = cols * CELL - ROOM_GAP
        content_h = rows * CELL - ROOM_GAP
        panel_w   = content_w + MINIMAP_PADDING * 2
        panel_h   = content_h + MINIMAP_PADDING * 2

        sw, sh = screen.get_size()
        panel_x = sw - MINIMAP_MARGIN - panel_w
        panel_y = MINIMAP_MARGIN

        # --- Draw panel background ---
        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel_surf.fill(_C["panel_bg"])
        screen.blit(panel_surf, (panel_x, panel_y))
        pygame.draw.rect(
            screen, _C["panel_border"],
            (panel_x, panel_y, panel_w, panel_h), 1, border_radius=4,
        )

        # --- Helper: grid pos → pixel center on screen ---
        def screen_pos(gx: int, gy: int) -> tuple[int, int]:
            lx = (gx - min_gx) * CELL + ROOM_SIZE // 2
            ly = (gy - min_gy) * CELL + ROOM_SIZE // 2
            return (panel_x + MINIMAP_PADDING + lx,
                    panel_y + MINIMAP_PADDING + ly)

        # --- Draw doors first (behind rooms) ---
        drawn_doors: set[tuple] = set()
        for pos, node in visited.items():
            for side, neighbour_pos in node.connections.items():
                # Avoid drawing each door twice
                edge_key = tuple(sorted((pos, neighbour_pos)))
                if edge_key in drawn_doors:
                    continue
                drawn_doors.add(edge_key)

                cx, cy = screen_pos(*pos)
                dx, dy = DIRECTIONS[side]

                neighbour_visited = neighbour_pos in visited
                door_color = _C["door"] if neighbour_visited else _C["door_to_unknown"]

                # Door line from room edge to midpoint of gap
                half_step = CELL // 2
                if dx != 0:
                    # Horizontal door
                    start_x = cx + dx * (ROOM_SIZE // 2)
                    end_x   = cx + dx * half_step
                    pygame.draw.line(
                        screen, door_color,
                        (start_x, cy), (end_x, cy),
                        DOOR_THICKNESS,
                    )
                else:
                    # Vertical door
                    start_y = cy + dy * (ROOM_SIZE // 2)
                    end_y   = cy + dy * half_step
                    pygame.draw.line(
                        screen, door_color,
                        (cx, start_y), (cx, end_y),
                        DOOR_THICKNESS,
                    )

        # --- Draw rooms ---
        for pos, node in visited.items():
            cx, cy = screen_pos(*pos)
            is_current = (node is current_node)
            color = _room_color(node, is_current)

            room_rect = pygame.Rect(
                cx - ROOM_SIZE // 2,
                cy - ROOM_SIZE // 2,
                ROOM_SIZE,
                ROOM_SIZE,
            )
            pygame.draw.rect(screen, color, room_rect, border_radius=2)

            # Thin highlight border on current room
            if is_current:
                pygame.draw.rect(
                    screen, (255, 255, 255),
                    room_rect.inflate(4, 4), 2, border_radius=3,
                )