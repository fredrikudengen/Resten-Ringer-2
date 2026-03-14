from rooms.grid_room import GridRoom
from rooms import room_data as data


def build_rooms() -> dict[str, list[GridRoom]]:
    return {
        "combat": [GridRoom(layout, room_type="combat") for layout in data.COMBAT],
        "elite":  [GridRoom(layout, room_type="elite")  for layout in data.ELITE],
        "boss":   [GridRoom(layout, room_type="boss")   for layout in data.BOSS],
        "reward": [GridRoom(layout, room_type="reward") for layout in data.REWARD],
        "start":  [GridRoom(layout, room_type="start")  for layout in data.START],
    }