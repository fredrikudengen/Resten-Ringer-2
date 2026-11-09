# Importer fra undermodulene direkte (src.core.world, src.core.ui, ...).
# Pakken importerer ingenting selv: world.py avhenger av src.entities, og src.entities
# avhenger av src.core.constants, så en eager import her gir sirkulær import.
