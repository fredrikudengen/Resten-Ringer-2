import random

from .floor_map import FloorMap, RoomNode, DIRECTIONS

# ===========================================================================
# ETASJE-GENERATOR — Her kan du justere størrelse og form på etasjene
# ===========================================================================
#
# Hvordan etasjer bygges:
#   1. En "hovedsti" fra startrom til bossrom genereres først
#   2. Sidegrener vokser ut fra hovedstien
#   3. Romtyper tildeles etterpå (combat, reward, elite, boss)
#
# Tips: Øk MAX_TOTAL_ROOMS og BRANCH_CHANCE for større, mer labyrintiske etasjer.
#       Senk MIN_MAIN_PATH for kortere vei til bossen.
# ===========================================================================

# --- Hovedsti ---
MIN_MAIN_PATH = 5  # Minimum antall rom på hovedstien (inkl. start + boss)
MAX_MAIN_PATH = 7  # Maksimum antall rom på hovedstien

# --- Total størrelse ---
MIN_TOTAL_ROOMS = 10  # Kast etasjen og prøv igjen hvis færre rom enn dette
MAX_TOTAL_ROOMS = 18  # Stopp å grene ut når vi når dette antallet rom

MAX_RETRIES = 30  # Maks antall forsøk før vi gir opp (skal sjelden treffe)

# --- Retningsbias ---
# Høyere verdi = stien fortsetter oftere i samme retning → mer lineær følelse
# Lavere verdi = stien svinger mer → mer labyrintisk
DIRECTION_BIAS = 0.45

# --- Grener ---
# BRANCH_CHANCE: sannsynlighet for at et rom på hovedstien får en gren (0.0–1.0)
# BRANCH_DECAY:  multipliseres med BRANCH_CHANCE for hver nivå av undergrener
# BRANCH_MAX_LENGTH: maks rom i én gren
# BRANCH_MAX_DEPTH:  maks nivåer av undergrener (2 = grener kan ha egne grener)
BRANCH_CHANCE = 0.55
BRANCH_DECAY = 0.45
BRANCH_MAX_LENGTH = 4
BRANCH_MAX_DEPTH = 2

# --- Romtyper for blindveier ---
# Blindveier (rom med kun én forbindelse) får en tilfeldig type fra denne listen.
# Juster vektene for å endre hyppigheten av hver type.
# "combat" = vanlig kamperom, "reward" = belønningsrom, "elite" = eliterom
_DEADEND_WEIGHTS: list[tuple[str, float]] = [
    ("combat",  0.35),
    ("reward",  0.30),
    ("elite",   0.35),
]


def generate_floor(floor_number: int = 1) -> FloorMap:
    """
    Generer et komplett etasjekart.

    Prøver på nytt internt hvis resultatet er for lite. Kaster RuntimeError
    hvis MAX_RETRIES er nådd (skal ikke skje med fornuftige parametere).
    """
    for _ in range(MAX_RETRIES):
        floor_map = _try_generate(floor_number)
        if floor_map is not None and floor_map.room_count >= MIN_TOTAL_ROOMS:
            _assign_room_types(floor_map)
            return floor_map

    raise RuntimeError(
        f"FloorGenerator: failed to generate a valid floor after {MAX_RETRIES} retries"
    )

# ----------- HELPERS ----------

def _try_generate(floor_number: int) -> FloorMap | None:
    floor_map = FloorMap(floor_number=floor_number)
    occupied: set[tuple[int, int]] = set()

    path_length = random.randint(MIN_MAIN_PATH, MAX_MAIN_PATH)
    main_path = _grow_path(
        start=(0, 0),
        length=path_length,
        occupied=occupied,
    )
    if len(main_path) < MIN_MAIN_PATH:
        return None

    for pos in main_path:
        floor_map.add_node(RoomNode(gx=pos[0], gy=pos[1], room_type="combat"))
    floor_map.start_pos = main_path[0]
    floor_map.boss_pos  = main_path[-1]

    for i in range(len(main_path) - 1):
        a = floor_map.get_node(*main_path[i])
        b = floor_map.get_node(*main_path[i + 1])
        side = _side_between(main_path[i], main_path[i + 1])
        floor_map.connect(a, side, b)

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
    Tilfeldig vandring som prøver å nå *length* rom.
    Bruker retningsbias: vandringen foretrekker å fortsette i samme retning.
    """
    path = [start]
    occupied.add(start)
    prev_dir: str | None = None
    sides = list(DIRECTIONS.keys())

    for _ in range(length - 1):
        current = path[-1]
        random.shuffle(sides)

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

def _assign_room_types(floor_map: FloorMap):
    """
    Tilordner romtyper etter generering.

    Regler:
      - Startrom  → "start"
      - Bossrom   → "boss"
      - Blindveier (1 forbindelse, ikke start/boss) → vektet tilfeldig
      - Alt annet → "combat"
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

def _side_between(a: tuple[int, int], b: tuple[int, int]) -> str:
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    for side, (sx, sy) in DIRECTIONS.items():
        if (sx, sy) == (dx, dy):
            return side
    raise ValueError(f"Positions {a} and {b} are not adjacent")

def _pick_biased(candidates: list[str], preferred: str | None) -> str:
    if preferred and preferred in candidates and random.random() < DIRECTION_BIAS:
        return preferred
    return random.choice(candidates)


def _weighted_choice(weights: list[tuple[str, float]]) -> str:
    names, ws = zip(*weights)
    return random.choices(names, weights=ws, k=1)[0]