"""Calcolo delle statistiche dei giocatori (senza dipendenze da Django)."""
import datetime

from .rules import POINTS


def _pct(won, played):
    return round(100 * won / played, 1) if played else 0


def _empty():
    return {"played": 0, "won": 0, "points": 0, "legs_played": 0, "legs_won": 0}


def _add(stat, mine, theirs):
    stat["played"] += 1
    stat["won"] += 1 if mine > theirs else 0
    stat["points"] += POINTS.get((mine, theirs), 0)
    stat["legs_played"] += mine + theirs
    stat["legs_won"] += mine


def player_stats(matches, our_team_id):
    """Classifica dei nostri giocatori, con il dettaglio partita per partita.

    La percentuale è calcolata sui match vinti, non sui leg.
    """
    stats = {}
    for m in matches:
        fx = m.fixture
        is_home = fx.home_team_id == our_team_id
        opponent = fx.away_team if is_home else fx.home_team
        players = (m.home_p1, m.home_p2) if is_home else (m.away_p1, m.away_p2)
        mine, theirs = (m.home_score, m.away_score) if is_home else (m.away_score, m.home_score)
        for p in players:
            if p is None:
                continue
            s = stats.setdefault(p.id, {"player": p, **_empty(), "fixtures": {}})
            _add(s, mine, theirs)
            f = s["fixtures"].setdefault(
                fx.id, {"fixture": fx, "opponent": opponent, "is_home": is_home, **_empty()}
            )
            _add(f, mine, theirs)

    rows = list(stats.values())
    for s in rows:
        s["pct"] = _pct(s["won"], s["played"])
        fixtures = list(s["fixtures"].values())
        for f in fixtures:
            f["pct"] = _pct(f["won"], f["played"])
        fixtures.sort(key=lambda f: (f["fixture"].date or datetime.date.min, f["fixture"].number))
        s["fixtures"] = fixtures
    rows.sort(key=lambda s: (-s["points"], -s["pct"], s["player"].name))
    return rows
