# Resten Ringer 2 — Playtest-build

Takk for at du tar deg tid til å teste spillet!

Dette er et tidlig build av et roguelike-spill laget i Python og Pygame. Oppfølgeren til kult-klassikeren Resten Ringer.
Jeg er setter pris på tilbakemeldinger på balanse, fiendeatferd, kontroller og generell spillfølelse.

---

## Kom i gang

### Krav
- Python 3.11 eller nyere
- Pygame: `pip install pygame`

### Kloning
- git clone https://github.com/fredrikudengen/Resten-Ringer-2.git
- cd /stien/til/Resten Ringer 2
- pip install pygame
- python main.py

---

## Kontroller

| Tast / Knapp     | Handling                |
|------------------|-------------------------|
| **WASD**         | Beveg spilleren         |
| **Venstreklikk** | Skyt                    |
| **Spacebar**     | Dash                    |
| **R**            | Reload                  |
| **ESC**          | Pause / avvis belønning |

---

## Hva du kan justere — og hvor

Alle tallverdier i spillet er samlet øverst i filene med kommentarer.
Her er en oversikt over hva du finner hvor:

### Floor — `entities/floor/floor_generator.py`
Kontrollerer størrelsen og formen på etasjene:
- **`MIN_MAIN_PATH` / `MAX_MAIN_PATH`** — Lengden på stien fra start til boss
- **`MIN_TOTAL_ROOMS` / `MAX_TOTAL_ROOMS`** — Total størrelse på etasjen
- **`BRANCH_CHANCE`** — Sannsynligheten for sidegrener (høyere = mer labyrintisk)
- **`_DEADEND_WEIGHTS`** — Fordeling mellom combat-, reward- og elite-rom i blindrom/blindveier

### Vanlige fiender — `entities/enemies/enemy_types.py`
- **`SwarmEnemy`** — Liten og rask, farlig i flokk
- **`FastEnemy`** — Rask melee-fiende
- **`ShooterEnemy`** — Holder avstand og skyter med pistol
- **`MarksmanEnemy`** — Langtrekkende rifle-fiende

Justerbare verdier per fiende: `speed`, `health`, `damage`, `attack_cooldown`, `detection_radius`, `knockback_strength`

### Elitefiender — `entities/enemies/elite_enemies.py`
- **`ScoutEnemy`** — Vet alltid hvor du er, ingen deteksjonsradius
- **`AssassinEnemy`** — Rask melee + lunge-angrep
- **`SlowEnemy`** — Treg men høy skade, windup-angrep
- **`BruteEnemy`** — Stor og tøff, lang windup
- **`TankEnemy`** — Mest liv, høy skade

Spesielle verdier for AssassinEnemy: `_LUNGE_SPEED`, `_LUNGE_COOLDOWN`, `_lunge_windup`

### Boss — `entities/enemies/boss_enemies.py`
- **`WardenBoss`** — To-phase boss med lunge-angrep og minion-spawning
- Justerbare verdier: `health`, `attack_windup_ms`, `_LUNGE_SPEED`, `_PHASE1_SPAWN_INTERVAL`, `_MINION_CAP`

### Vanskelighetsgrad og progresjon — `entities/enemies/progression.py`
- **`_THRESHOLDS`** — Hvor mange rom som ryddes mellom hvert progression level
- **`ENEMY_POOL`** — Hvilke fiender som kan spawne på hvert level
- **`scale_enemy()`** — HP- og skade-multipliers per level (se kommentarer i filen)

---

## Kjente begrensninger i dette buildet

- Ingen lyd (kommer)
- Ingen sprites — alle enheter er rektangler for nå
- Kun én boss (Warden)
- Balansen er ikke ferdig

---

## Tilbakemelding jeg er ute etter

Jeg setter stor pris på tilbakemeldinger på alt, men da særlig:

**Spillfølelse og balanse**
- Føles kontrollene responsive?
- Er noen fiender for lette / for vanskelige?
- Er det noen punkter i spillet som føles kjedelige eller frustrerende?
- Hvordan oppleves bossen? For lett, for vanskelig, eller akkurat passe?

**Ideer til nye fiender**
Har du ideer til fiender med interessante mekanikker?

**Ideer til powerups og oppgraderinger**
Spillet har noen grunnleggende powerups. Hva slags oppgraderinger hadde vært morsomme?

**Ideer til sprites / visuell stil**

---

## Send tilbakemelding

- Åpne et **[GitHub Issue](https://github.com/fredrikudengen/Resten-Ringer-2/issues/new/choose)**

Alle tilbakemeldinger hjelper!
