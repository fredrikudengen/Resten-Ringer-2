from rooms.grid_room import GridRoom
from rooms import room_data as data

def build_rooms() -> dict:
    return {
        "combat": [GridRoom(layout) for layout in data.COMBAT],
        "elite":  [GridRoom(layout) for layout in data.ELITE],
        "boss":   [GridRoom(layout) for layout in data.BOSS],
        "reward": [GridRoom(layout) for layout in data.REWARD],
        "start":  [GridRoom(layout) for layout in data.START],
    }