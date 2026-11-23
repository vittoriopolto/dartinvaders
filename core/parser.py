"""Lettura del testo del referto (formato standard), senza dipendenze da Django."""
import re
from dataclasses import dataclass, field
import datetime as dt

from .rules import VALID_SCORES, team_points

HEADER_RE = re.compile(
    r"^(CAMPIONATO|PARTITA|TURNO|DATA|LUOGO|CASA|OSPITE|TOTALE)\s*:\s*(.*)$", re.I
)


@dataclass
class ParsedMatch:
    code: str
    home: list
    away: list
    home_score: int
    away_score: int


@dataclass
class ParsedReport:
    championship: str = ""
    number: int | None = None
    turn: str = ""
    date: dt.date | None = None
    venue: str = ""
    home_team: str = ""
    home_captain: str = ""
    away_team: str = ""
    away_captain: str = ""
    players: dict = field(default_factory=dict)  # codice -> (nome, tessera)
    matches: list = field(default_factory=list)
    declared: dict = field(default_factory=dict)
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)

    @property
    def totals(self):
        hs = sum(1 for m in self.matches if m.home_score > m.away_score)
        return {
            "home_sets": hs,
            "away_sets": len(self.matches) - hs,
            "home_legs": sum(m.home_score for m in self.matches),
            "away_legs": sum(m.away_score for m in self.matches),
        }

    @property
    def roster_home(self):
        return [(c, n, t) for c, (n, t) in self.players.items() if c.startswith("C")]

    @property
    def roster_away(self):
        return [(c, n, t) for c, (n, t) in self.players.items() if c.startswith("O")]

    def rows(self):
        def names(codes):
            return " + ".join(self.players[c][0] for c in codes if c in self.players)

        return [
            {
                "code": m.code,
                "home": names(m.home),
                "score": f"{m.home_score}-{m.away_score}",
                "away": names(m.away),
            }
            for m in self.matches
        ]


def _split_team(value):
    parts = [p.strip() for p in value.split("|")]
    captain = ""
    for p in parts[1:]:
        m = re.match(r"capitano\s*:\s*(.+)", p, re.I)
        if m:
            captain = m.group(1).strip()
    return parts[0], captain


def _parse_date(value):
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d/%m/%y", "%d-%m-%Y"):
        try:
            return dt.datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue
    return None


def parse_report(text):
    r = ParsedReport()

    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("```"):
            continue

        h = HEADER_RE.match(line)
        if h:
            key, val = h.group(1).upper(), h.group(2).strip()
            if key == "CAMPIONATO":
                r.championship = val
            elif key == "PARTITA":
                if val.isdigit():
                    r.number = int(val)
                else:
                    r.errors.append(f"Riga {n}: il numero partita non è valido ({val}).")
            elif key == "TURNO":
                r.turn = val
            elif key == "DATA":
                r.date = _parse_date(val)
                if r.date is None:
                    r.errors.append(f"Riga {n}: data non valida ({val}). Usa AAAA-MM-GG o GG/MM/AAAA.")
            elif key == "LUOGO":
                r.venue = val
            elif key == "CASA":
                r.home_team, r.home_captain = _split_team(val)
            elif key == "OSPITE":
                r.away_team, r.away_captain = _split_team(val)
            elif key == "TOTALE":
                for name in ("legs", "set", "punti"):
                    m = re.search(rf"{name}\s*(\d+)\s*-\s*(\d+)", val, re.I)
                    if m:
                        r.declared[name] = (int(m.group(1)), int(m.group(2)))
            continue

        parts = [p.strip() for p in line.split("|")]
        code = parts[0].upper()

        if re.fullmatch(r"[CO]\d+", code):
            if len(parts) < 2 or not parts[1]:
                r.errors.append(f"Riga {n}: manca il nome del giocatore {code}.")
                continue
            tessera = parts[2] if len(parts) > 2 and parts[2] else None
            r.players[code] = (re.sub(r"\s+", " ", parts[1]), tessera)

        elif re.fullmatch(r"[SD]\d+", code):
            if len(parts) != 4:
                r.errors.append(f"Riga {n}: il match {code} deve avere 4 campi (codice | casa | risultato | ospite).")
                continue
            home = [c.strip().upper() for c in parts[1].split("+")]
            away = [c.strip().upper() for c in parts[3].split("+")]
            need = 1 if code[0] == "S" else 2
            if len(home) != need or len(away) != need:
                r.errors.append(f"Riga {n}: {code} richiede {need} giocatore/i per squadra.")
                continue
            sm = re.fullmatch(r"(\d)\s*-\s*(\d)", parts[2])
            if not sm or (int(sm.group(1)), int(sm.group(2))) not in VALID_SCORES:
                r.errors.append(f"Riga {n}: risultato non valido per {code} ({parts[2]}). Ammessi: 2-0, 2-1, 1-2, 0-2.")
                continue
            r.matches.append(ParsedMatch(code, home, away, int(sm.group(1)), int(sm.group(2))))

        else:
            r.errors.append(f"Riga {n}: riga non riconosciuta ({line[:40]}).")

    # Controlli finali
    if not r.championship:
        r.errors.append("Manca la riga CAMPIONATO.")
    if r.number is None and not any("numero partita" in e for e in r.errors):
        r.errors.append("Manca la riga PARTITA.")
    if not r.home_team or not r.away_team:
        r.errors.append("Servono le righe CASA e OSPITE.")
    elif r.home_team.lower() == r.away_team.lower():
        r.errors.append("Squadra di casa e ospite coincidono.")
    if not r.matches:
        r.errors.append("Non ci sono match (righe S1, S2… e D1, D2…).")

    for m in r.matches:
        for c in m.home:
            if c not in r.players or not c.startswith("C"):
                r.errors.append(f"{m.code}: il giocatore di casa {c} non è nell'elenco.")
        for c in m.away:
            if c not in r.players or not c.startswith("O"):
                r.errors.append(f"{m.code}: il giocatore ospite {c} non è nell'elenco.")

    if r.matches and not r.errors:
        singles = sum(1 for m in r.matches if m.code.startswith("S"))
        doubles = len(r.matches) - singles
        if (singles, doubles) != (16, 4):
            r.warnings.append(f"Trovati {singles} singoli e {doubles} doppi (attesi 16 e 4).")
        t = r.totals
        if "legs" in r.declared and r.declared["legs"] != (t["home_legs"], t["away_legs"]):
            r.warnings.append(
                f"Leg del TOTALE {r.declared['legs'][0]}-{r.declared['legs'][1]}, "
                f"ma dai match risultano {t['home_legs']}-{t['away_legs']}."
            )
        if "set" in r.declared and r.declared["set"] != (t["home_sets"], t["away_sets"]):
            r.warnings.append(
                f"Set del TOTALE {r.declared['set'][0]}-{r.declared['set'][1]}, "
                f"ma dai match risultano {t['home_sets']}-{t['away_sets']}."
            )
        if "punti" in r.declared:
            calc = team_points(t["home_sets"], t["away_sets"], t["home_legs"], t["away_legs"])
            if r.declared["punti"] != calc:
                r.warnings.append(
                    f"Punti del TOTALE {r.declared['punti'][0]}-{r.declared['punti'][1]}, "
                    f"ma dalle regole risultano {calc[0]}-{calc[1]}."
                )
    return r
