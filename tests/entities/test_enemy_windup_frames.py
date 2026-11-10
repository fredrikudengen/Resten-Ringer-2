import os


from entities.enemies.elite_enemies import SlowEnemy, BruteEnemy, TankEnemy, WindupMeleeMixin
from fakes import set_ticks, OpenRoom, FakePlayer

DT = 16
MELEE = (SlowEnemy, BruteEnemy, TankEnemy)
ASSETS = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "sprites")


def _make(cls, monkeypatch, now=1000):
    set_ticks(monkeypatch, now)
    monkeypatch.setattr(cls, "stat_spread", 0)
    enemy = cls(2000, 2000)
    enemy.state = "chase"
    enemy.dir_noise_deg = 0
    return enemy


def test_melee_sprites_have_windup_and_strike_frames_on_disk():
    for cls in MELEE:
        enemy = cls(0, 0)
        for frame in ("windup", "strike"):
            assert enemy.sprite.has_frame(frame), (cls.__name__, frame)
            path = enemy.sprite._animations[frame][0]
            assert os.path.isfile(os.path.join(ASSETS, path + ".png")), path


def test_windup_frame_during_attack_then_strike_then_walk(monkeypatch):
    for cls in MELEE:
        enemy = _make(cls, monkeypatch)
        player = FakePlayer((enemy.rect.centerx + 40, enemy.rect.centery))
        room = OpenRoom()

        assert enemy._sprite_frame() == "walk"   # jager → går

        enemy.move(player, [], room, DT)
        assert enemy.state == "attack", cls.__name__
        assert enemy._sprite_frame() == "windup"

        hit_at = 1000 + cls.attack_windup_ms
        set_ticks(monkeypatch, hit_at)
        enemy.move(player, [], room, DT)
        assert enemy.state == "chase"
        assert enemy._sprite_frame() == "strike", cls.__name__

        set_ticks(monkeypatch, hit_at + WindupMeleeMixin._STRIKE_MS - 1)
        assert enemy._sprite_frame() == "strike"

        set_ticks(monkeypatch, hit_at + WindupMeleeMixin._STRIKE_MS)
        assert enemy._sprite_frame() == "walk"


def test_brute_lunge_uses_windup_and_strike_frames(monkeypatch):
    enemy = _make(BruteEnemy, monkeypatch)
    player = FakePlayer((enemy.rect.centerx + 250, enemy.rect.centery))

    enemy.move(player, [], OpenRoom(), DT)
    assert enemy.state == "lunge_windup"
    assert enemy._sprite_frame() == "windup"

    set_ticks(monkeypatch, 1000 + BruteEnemy._LUNGE_WINDUP + 1)
    enemy.move(player, [], OpenRoom(), DT)
    assert enemy.state == "lunge"
    assert enemy._sprite_frame() == "strike"


def test_standing_enemy_shows_idle_and_falls_back_without_walk_frames(monkeypatch):
    slow = _make(SlowEnemy, monkeypatch)
    slow.state = "idle"
    slow.wander_goal_g = None
    assert slow._visual_frame() == "idle"

    tank = _make(TankEnemy, monkeypatch)       # har ingen walk-frames
    assert tank._sprite_frame() == "walk"
    assert tank._visual_frame() == "idle"


def test_slow_windup_spans_the_whole_windup_once():
    enemy = SlowEnemy(0, 0)
    frames = enemy.sprite._animations["windup"]
    duration = enemy.sprite._frame_durations["windup"]
    assert duration * len(frames) == enemy.attack_windup_ms
    assert "windup" in enemy.sprite._play_once
    for path in frames + enemy.sprite._animations["walk"]:
        assert os.path.isfile(os.path.join(ASSETS, path + ".png")), path
