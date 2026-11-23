from django.conf import settings
from django.db.models import Q

from .aggregate import player_stats
from .models import Match, Team


def get_our_team():
    return Team.objects.filter(name__iexact=settings.OUR_TEAM_NAME).first()


def our_player_stats():
    """Classifica dei giocatori della nostra squadra, calcolata da tutti i match."""
    our = get_our_team()
    if our is None:
        return []
    matches = Match.objects.filter(
        Q(fixture__home_team=our) | Q(fixture__away_team=our)
    ).select_related(
        "fixture", "fixture__home_team", "fixture__away_team",
        "home_p1", "home_p2", "away_p1", "away_p2",
    )
    return player_stats(matches, our.id)
