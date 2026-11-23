"""Regole del punteggio (senza dipendenze da Django)."""

# Risultati ammessi per un match, nella forma (leg casa, leg ospite).
VALID_SCORES = {(2, 0), (2, 1), (1, 2), (0, 2)}

# Punti individuali assegnati a chi ha fatto il primo numero del risultato.
POINTS = {(2, 0): 3, (2, 1): 2, (1, 2): 1, (0, 2): 0}


def team_points(home_sets, away_sets, home_legs, away_legs):
    """Punti di squadra per la partita (regolamento del referto).

    Più della metà dei set: 3-0. Metà esatta: vince chi ha più leg (2-1),
    altrimenti pareggio (1-1). Meno della metà: 0-3.
    """
    total = home_sets + away_sets
    if not total:
        return (0, 0)
    if home_sets * 2 > total:
        return (3, 0)
    if home_sets * 2 < total:
        return (0, 3)
    if home_legs > away_legs:
        return (2, 1)
    if home_legs < away_legs:
        return (1, 2)
    return (1, 1)
