from pathlib import Path

_MAPS = Path(__file__).parent / "maps"

def load_category(folder: str) -> list[list[str]]:
    """Laster alle .txt-filer i en mappe, sortert etter navn."""
    return [
        p.read_text().splitlines()
        for p in sorted((_MAPS / folder).glob("*.txt"))
    ]

COMBAT = load_category("combat")
ELITE  = load_category("elite")
BOSS   = load_category("boss")
REWARD = load_category("reward")
START  = load_category("start")