from types import SimpleNamespace

from gamestates.boss_reward import _STAT_UPGRADES as BOSS_UPGRADES
from gamestates.room_reward import _STAT_UPGRADES as ROOM_UPGRADES


def _ammo_upgrade(upgrades):
    return next(u for u in upgrades if "Max Ammo" in u["label"])


def test_boss_ammo_upgrade_matches_its_label():
    upgrade = _ammo_upgrade(BOSS_UPGRADES)
    player = SimpleNamespace(gun=SimpleNamespace(max_ammo=12))
    upgrade["apply"](player)
    assert upgrade["label"] == "+30% Max Ammo"
    assert player.gun.max_ammo == 16


def test_ammo_upgrade_keeps_infinite_ammo_infinite():
    # max_ammo = -1 betyr uendelig (standard i Gun). "+2" ville gjort det om til 1 skudd
    for upgrades in (BOSS_UPGRADES, ROOM_UPGRADES):
        player = SimpleNamespace(gun=SimpleNamespace(max_ammo=-1))
        _ammo_upgrade(upgrades)["apply"](player)
        assert player.gun.max_ammo < 0
