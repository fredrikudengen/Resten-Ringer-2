from pathlib import Path

_MAPS = Path(__file__).parent / "maps"

import os
_MAPS = Path(__file__).parent / "maps"
print("DEBUG __file__:", __file__)
print("DEBUG _MAPS:", _MAPS)
print("DEBUG _MAPS.resolve():", _MAPS.resolve())
print("DEBUG cwd:", os.getcwd())
print("DEBUG start folder exists:", (_MAPS / "start").is_dir())

def _read_map(path: Path) -> list[str]:
    """Leser en kartfil og fjerner tomme linjer på slutten.

    En etterfølgende blank linje ville ellers telt som en ekstra rad, slik at
    GridRoom._tile_side ikke lenger kjenner igjen nederste rad som "S" – og
    dørene der blir stille gjort om til vegg.
    """
    lines = path.read_text().splitlines()
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def load_category(folder: str) -> list[list[str]]:
    """Laster alle .txt-filer i en mappe, sortert etter navn."""
    return [
        _read_map(p)
        for p in sorted((_MAPS / folder).glob("*.txt"))
    ]

COMBAT = load_category("combat")
ELITE  = load_category("elite")
BOSS   = load_category("boss")
REWARD = load_category("reward")
START  = load_category("start")