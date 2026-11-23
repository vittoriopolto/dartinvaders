from django import forms
from django.forms import modelformset_factory

from .models import Fixture, Match, Player


class FixtureForm(forms.ModelForm):
    class Meta:
        model = Fixture
        fields = [
            "championship", "number", "turn", "date", "venue",
            "home_team", "away_team", "home_captain", "away_captain",
        ]
        widgets = {"date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")}


PLAYER_FIELDS = ("home_p1", "home_p2", "away_p1", "away_p2")


class MatchForm(forms.ModelForm):
    class Meta:
        model = Match
        fields = ["home_p1", "home_p2", "home_score", "away_score", "away_p1", "away_p2"]
        widgets = {
            "home_score": forms.NumberInput(attrs={"min": 0, "max": 2}),
            "away_score": forms.NumberInput(attrs={"min": 0, "max": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        players = Player.objects.select_related("team").order_by("name")
        for name in PLAYER_FIELDS:
            field = self.fields[name]
            field.queryset = players
            field.label_from_instance = lambda p: f"{p.name} ({p.team.name})"


MatchFormSet = modelformset_factory(Match, form=MatchForm, extra=0)
