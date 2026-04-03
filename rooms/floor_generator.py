from __future__ import annotations

import random

from .floor_map import FloorMap, RoomNode, DIRECTIONS


# ---- Floor generator variables ----

MIN_MAIN_PATH     = 7      # minimum rooms on the main path (including start + boss)
MAX_MAIN_PATH     = 10     # maximum main path length
MIN_TOTAL_ROOMS   = 14     # discard and retry if fewer rooms than this
MAX_TOTAL_ROOMS   = 22     # stop branching once we reach this count
MAX_RETRIES       = 30     # give up after this many failed attempts
DIRECTION_BIAS    = 0.45   # probability of continuing in same direction
BRANCH_CHANCE     = 0.55   # base chance a main-path room spawns a branch
BRANCH_DECAY      = 0.45   # multiply branch chance each level of sub-branching
BRANCH_MAX_LENGTH = 4      # max rooms in a single branch
BRANCH_MAX_DEPTH  = 2      # how many levels of sub-branching allowed

# Room type weights for dead-end rooms (non-boss, non-start)
_DEADEND_WEIGHTS: list[tuple[str, float]] = [
    ("combat",  0.45),
    ("reward",  0.70),
    ("elite",   0.25),
]


def generate_floor(floor_number: int = 1) -> FloorMap:
    """
    Generate a full floor map.

    Retries internally if the result is too small. Raises RuntimeError
    if MAX_RETRIES is exhausted (shouldn't happen with reasonable params).

    Parameters
    ----------
    floor_number : int
        Current floor (1-based). Stored on the FloorMap for difficulty scaling.
        Could influence generation params in the future.
    """
    for _ in range(MAX_RETRIES):
        floor_map = _try_generate(floor_number)
        if floor_map is not None and floor_map.room_count >= MIN_TOTAL_ROOMS:
            _assign_room_types(floor_map)
            return floor_map

    raise RuntimeError(
        f"FloorGenerator: failed to generate a valid floor after {MAX_RETRIES} retries"
    )


# ---------------------------------------------------------------------------
# Internal generation
# ---------------------------------------------------------------------------

def _try_generate(floor_number: int) -> FloorMap | None:
    """One generation attempt.  Returns None if the main path is too short."""
    floor_map = FloorMap(floor_number=floor_number)
    occupied: set[tuple[int, int]] = set()

    # --- Main path ---
    path_length = random.randint(MIN_MAIN_PATH, MAX_MAIN_PATH)
    main_path = _grow_path(
        start=(0, 0),
        length=path_length,
        occupied=occupied,
    )
    if len(main_path) < MIN_MAIN_PATH:
        return None

    # Create nodes for the main path
    for pos in main_path:
        floor_map.add_node(RoomNode(gx=pos[0], gy=pos[1], room_type="combat"))
    floor_map.start_pos = main_path[0]
    floor_map.boss_pos  = main_path[-1]

    # Connect consecutive main-path rooms
    for i in range(len(main_path) - 1):
        a = floor_map.get_node(*main_path[i])
        b = floor_map.get_node(*main_path[i + 1])
        side = _side_between(main_path[i], main_path[i + 1])
        floor_map.connect(a, side, b)

    # --- Branches ---
    # Pick random rooms along the main path (skip start and boss) as branch roots
    branch_candidates = main_path[1:-1]
    random.shuffle(branch_candidates)

    for pos in branch_candidates:
        if floor_map.room_count >= MAX_TOTAL_ROOMS:
            break
        if random.random() < BRANCH_CHANCE:
            _grow_branch(
                floor_map=floor_map,
                root_pos=pos,
                occupied=occupied,
                depth=0,
            )

    return floor_map


def _grow_path(
    start: tuple[int, int],
    length: int,
    occupied: set[tuple[int, int]],
) -> list[tuple[int, int]]:
    """
    Random walk that tries to reach *length* rooms.

    Uses directional bias: the walk prefers to continue in the same
    direction it was already going, giving the path a natural flow
    without forcing a fixed axis.
    """
    path = [start]
    occupied.add(start)
    prev_dir: str | None = None
    sides = list(DIRECTIONS.keys())

    for _ in range(length - 1):
        current = path[-1]
        random.shuffle(sides)

        # Build a weighted candidate list favouring prev_dir
        candidates: list[str] = []
        for s in sides:
            dx, dy = DIRECTIONS[s]
            neighbour = (current[0] + dx, current[1] + dy)
            if neighbour in occupied:
                continue
            candidates.append(s)

        if not candidates:
            break

        chosen = _pick_biased(candidates, prev_dir)
        dx, dy = DIRECTIONS[chosen]
        next_pos = (current[0] + dx, current[1] + dy)

        path.append(next_pos)
        occupied.add(next_pos)
        prev_dir = chosen

    return path


def _grow_branch(
    floor_map: FloorMap,
    root_pos: tuple[int, int],
    occupied: set[tuple[int, int]],
    depth: int,
):
    """
    Grow a branch off an existing room.  May recursively sub-branch.
    """
    if depth > BRANCH_MAX_DEPTH:
        return
    if floor_map.room_count >= MAX_TOTAL_ROOMS:
        return

    root_node = floor_map.get_node(*root_pos)
    if root_node is None:
        return

    sides = list(DIRECTIONS.keys())
    random.shuffle(sides)
    start_side: str | None = None
    first_pos: tuple[int, int] | None = None

    for s in sides:
        dx, dy = DIRECTIONS[s]
        candidate = (root_pos[0] + dx, root_pos[1] + dy)
        if candidate not in occupied:
            start_side = s
            first_pos = candidate
            break

    if start_side is None or first_pos is None:
        return

    branch_length = random.randint(1, BRANCH_MAX_LENGTH)
    branch_path = _grow_path(first_pos, branch_length, occupied)

    if not branch_path:
        return

    for pos in branch_path:
        floor_map.add_node(RoomNode(gx=pos[0], gy=pos[1], room_type="combat"))

    floor_map.connect(root_node, start_side, floor_map.get_node(*branch_path[0]))

    for i in range(len(branch_path) - 1):
        a = floor_map.get_node(*branch_path[i])
        b = floor_map.get_node(*branch_path[i + 1])
        side = _side_between(branch_path[i], branch_path[i + 1])
        floor_map.connect(a, side, b)

    for pos in branch_path:
        if floor_map.room_count >= MAX_TOTAL_ROOMS:
            break
        sub_chance = BRANCH_CHANCE * (BRANCH_DECAY ** (depth + 1))
        if random.random() < sub_chance:
            _grow_branch(floor_map, pos, occupied, depth + 1)


# ---------------------------------------------------------------------------
# Room type assignment
# ---------------------------------------------------------------------------

def _assign_room_types(floor_map: FloorMap):
    """
    Assign room types after generation.

    Rules:
      - Start room → "start"
      - Boss room  → "boss"
      - Dead ends (1 connection, not start/boss) → weighted random (combat/reward/elite)
      - Everything else → "combat"
    """
    for pos, node in floor_map.nodes.items():
        if pos == floor_map.start_pos:
            node.room_type = "start"
        elif pos == floor_map.boss_pos:
            node.room_type = "boss"
        elif len(node.connections) == 1:
            node.room_type = _weighted_choice(_DEADEND_WEIGHTS)
        else:
            node.room_type = "combat"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _side_between(a: tuple[int, int], b: tuple[int, int]) -> str:
    """Return the direction from a to b (must be adjacent)."""
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    for side, (sx, sy) in DIRECTIONS.items():
        if (sx, sy) == (dx, dy):
            return side
    raise ValueError(f"Positions {a} and {b} are not adjacent")


def _pick_biased(candidates: list[str], preferred: str | None) -> str:
    """
    Pick a direction from candidates, biased toward *preferred*.

    If preferred is in the list and the random roll hits, use it.
    Otherwise pick uniformly from the rest.
    """
    if preferred and preferred in candidates and random.random() < DIRECTION_BIAS:
        return preferred
    return random.choice(candidates)


def _weighted_choice(weights: list[tuple[str, float]]) -> str:
    """Simple weighted random selection."""
    names, ws = zip(*weights)
    return random.choices(names, weights=ws, k=1)[0]