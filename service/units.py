"""Shared unit table. Both workstreams import from here. Weights in kg.
A value of None means 'ambiguous: ask the farmer' with the listed options."""

UNITS = {
    # canonical: (aliases, kg_per_unit or None, options_if_ambiguous)
    "kg":    (["kg", "kilo", "kilos", "kilogram", "kilo moja"], 1.0, None),
    "basin": (["basin", "beseni", "bassin", "besheni"], None, {"1": 15.0, "2": 20.0}),
    "tin":   (["tin", "debe", "jerrican", "kasolo"], 20.0, None),
    "bag":   (["bag", "gunia", "sack", "saki", "ensawo", "magunia"], None, {"1": 90.0, "2": 100.0, "3": 120.0}),
}

CROPS = {
    "maize": ["maize", "mahindi", "kasooli", "maiz", "corn", "mais", "maindi"],
    "beans": ["beans", "maharagwe", "ebijanjaalo", "bean", "haragwe", "maharage"],
}

def alias_to_unit(token: str) -> str | None:
    t = token.lower().strip()
    for name, (aliases, _, _) in UNITS.items():
        if t in aliases:
            return name
    return None

def kg_for(unit: str, choice: str | None = None) -> float | None:
    aliases, kg, options = UNITS[unit]
    if kg is not None:
        return kg
    if choice and options and choice in options:
        return options[choice]
    return None
