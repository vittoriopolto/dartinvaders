from django.db import transaction

from .models import Championship, Fixture, Match, Player, Team


def _team(name):
    return Team.objects.filter(name__iexact=name).first() or Team.objects.create(name=name)


def _player(name, tessera, team):
    """Il giocatore si riconosce dalla tessera; senza tessera, da nome e squadra."""
    player = Player.objects.filter(tessera=tessera).first() if tessera else None
    if player is None:
        player = Player.objects.filter(name__iexact=name, team=team).first()
        if player and tessera and not player.tessera:
            player.tessera = tessera
            player.save(update_fields=["tessera"])
    if player is None:
        return Player.objects.create(name=name, tessera=tessera, team=team)
    if player.team_id != team.id:
        player.team = team
        player.save(update_fields=["team"])
    return player


@transaction.atomic
def save_report(r):
    """Salva un ParsedReport senza errori. Se la partita esiste già, la sostituisce."""
    championship, _ = Championship.objects.get_or_create(name=r.championship)
    home, away = _team(r.home_team), _team(r.away_team)
    players = {
        code: _player(name, tessera, home if code.startswith("C") else away)
        for code, (name, tessera) in r.players.items()
    }
    fixture, created = Fixture.objects.update_or_create(
        championship=championship,
        number=r.number,
        defaults={
            "turn": r.turn,
            "date": r.date,
            "venue": r.venue,
            "home_team": home,
            "away_team": away,
            "home_captain": r.home_captain,
            "away_captain": r.away_captain,
        },
    )
    fixture.matches.all().delete()

    def pick(codes, i):
        return players[codes[i]] if len(codes) > i else None

    Match.objects.bulk_create(
        Match(
            fixture=fixture,
            code=m.code,
            kind=m.code[0],
            order=i,
            home_p1=pick(m.home, 0),
            home_p2=pick(m.home, 1),
            away_p1=pick(m.away, 0),
            away_p2=pick(m.away, 1),
            home_score=m.home_score,
            away_score=m.away_score,
        )
        for i, m in enumerate(r.matches, 1)
    )
    return fixture, created
