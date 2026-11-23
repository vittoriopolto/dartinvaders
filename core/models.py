from django.core.exceptions import ValidationError
from django.db import models
from django.utils.functional import cached_property

from .rules import POINTS, VALID_SCORES, team_points


class Team(models.Model):
    name = models.CharField("nome", max_length=100, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "squadra"
        verbose_name_plural = "squadre"

    def __str__(self):
        return self.name


class Player(models.Model):
    name = models.CharField("nome e cognome", max_length=120)
    tessera = models.CharField("n° tessera", max_length=30, unique=True, null=True, blank=True)
    team = models.ForeignKey(Team, on_delete=models.PROTECT, related_name="players", verbose_name="squadra")

    class Meta:
        ordering = ["name"]
        verbose_name = "giocatore"
        verbose_name_plural = "giocatori"

    def __str__(self):
        return self.name


class Championship(models.Model):
    name = models.CharField("nome", max_length=200, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "campionato"
        verbose_name_plural = "campionati"

    def __str__(self):
        return self.name


class Fixture(models.Model):
    """Una partita tra due squadre (composta da 16 singoli e 4 doppi)."""

    championship = models.ForeignKey(
        Championship, on_delete=models.CASCADE, related_name="fixtures", verbose_name="campionato"
    )
    number = models.PositiveIntegerField("n° partita")
    turn = models.CharField("turno", max_length=60, blank=True)
    date = models.DateField("data", null=True, blank=True)
    venue = models.CharField("luogo", max_length=200, blank=True)
    home_team = models.ForeignKey(Team, on_delete=models.PROTECT, related_name="home_fixtures", verbose_name="squadra casa")
    away_team = models.ForeignKey(Team, on_delete=models.PROTECT, related_name="away_fixtures", verbose_name="squadra ospite")
    home_captain = models.CharField("capitano casa", max_length=120, blank=True)
    away_captain = models.CharField("capitano ospite", max_length=120, blank=True)

    class Meta:
        ordering = ["-date", "-number"]
        unique_together = [("championship", "number")]
        verbose_name = "partita"
        verbose_name_plural = "partite"

    def __str__(self):
        return f"{self.home_team} - {self.away_team} (n° {self.number})"

    @cached_property
    def totals(self):
        t = {"home_sets": 0, "away_sets": 0, "home_legs": 0, "away_legs": 0}
        for m in self.matches.all():
            t["home_legs"] += m.home_score
            t["away_legs"] += m.away_score
            if m.home_score > m.away_score:
                t["home_sets"] += 1
            else:
                t["away_sets"] += 1
        return t

    @cached_property
    def team_points(self):
        t = self.totals
        return team_points(t["home_sets"], t["away_sets"], t["home_legs"], t["away_legs"])

    def result_for(self, team_name):
        """'win', 'draw' o 'loss' dal punto di vista della squadra indicata ('' se non c'entra)."""
        h, a = self.team_points
        name = team_name.lower()
        if self.home_team.name.lower() == name:
            mine, theirs = h, a
        elif self.away_team.name.lower() == name:
            mine, theirs = a, h
        else:
            return ""
        return "win" if mine > theirs else "loss" if mine < theirs else "draw"


class Match(models.Model):
    """Un singolo (1 contro 1) o un doppio (2 contro 2). Il risultato è in leg."""

    SINGLE, DOUBLE = "S", "D"
    KINDS = [(SINGLE, "Singolo"), (DOUBLE, "Doppio")]

    fixture = models.ForeignKey(Fixture, on_delete=models.CASCADE, related_name="matches")
    code = models.CharField("codice", max_length=6)
    kind = models.CharField("tipo", max_length=1, choices=KINDS)
    order = models.PositiveSmallIntegerField("ordine", default=0)
    home_p1 = models.ForeignKey(Player, on_delete=models.PROTECT, related_name="+", null=True, blank=True)
    home_p2 = models.ForeignKey(Player, on_delete=models.PROTECT, related_name="+", null=True, blank=True)
    away_p1 = models.ForeignKey(Player, on_delete=models.PROTECT, related_name="+", null=True, blank=True)
    away_p2 = models.ForeignKey(Player, on_delete=models.PROTECT, related_name="+", null=True, blank=True)
    home_score = models.PositiveSmallIntegerField("leg casa")
    away_score = models.PositiveSmallIntegerField("leg ospite")

    class Meta:
        ordering = ["order"]
        verbose_name = "match"
        verbose_name_plural = "match"

    def __str__(self):
        return f"{self.code} {self.home_score}-{self.away_score}"

    def clean(self):
        if (self.home_score, self.away_score) not in VALID_SCORES:
            raise ValidationError("Risultato non valido: ammessi 2-0, 2-1, 1-2, 0-2.")

    @property
    def home_names(self):
        return " + ".join(p.name for p in (self.home_p1, self.home_p2) if p)

    @property
    def away_names(self):
        return " + ".join(p.name for p in (self.away_p1, self.away_p2) if p)

    @property
    def winner(self):
        return "home" if self.home_score > self.away_score else "away"

    @property
    def points_home(self):
        return POINTS.get((self.home_score, self.away_score), 0)

    @property
    def points_away(self):
        return POINTS.get((self.away_score, self.home_score), 0)
