from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .chart import build_chart
from .forms import FixtureForm, MatchFormSet
from .models import Fixture, Match
from .parser import parse_report
from .services import save_report
from .stats import our_player_stats

PLAYER_RELATED = ("home_p1", "home_p2", "away_p1", "away_p2")


def home(request):
    return render(
        request,
        "core/home.html",
        {"stats": our_player_stats(), "our_team": settings.OUR_TEAM_NAME},
    )


def fixture_list(request):
    fixtures = (
        Fixture.objects.select_related("championship", "home_team", "away_team")
        .prefetch_related("matches")
        .order_by("championship__name", "-date", "-number")
    )
    ours = settings.OUR_TEAM_NAME.lower()
    raw = []
    for f in fixtures:
        f.outcome = f.result_for(settings.OUR_TEAM_NAME)
        t = f.totals
        if f.home_team.name.lower() == ours:
            won, lost, opponent = t["home_sets"], t["away_sets"], f.away_team.name
        elif f.away_team.name.lower() == ours:
            won, lost, opponent = t["away_sets"], t["home_sets"], f.home_team.name
        else:
            continue
        raw.append({"id": f.pk, "turn": f.turn, "date": f.date, "won": won, "lost": lost, "opponent": opponent})
    return render(
        request,
        "core/fixture_list.html",
        {"fixtures": fixtures, "chart": build_chart(raw)},
    )


def fixture_detail(request, pk):
    fixture = get_object_or_404(
        Fixture.objects.select_related("championship", "home_team", "away_team").prefetch_related(
            Prefetch("matches", queryset=Match.objects.select_related(*PLAYER_RELATED))
        ),
        pk=pk,
    )
    matches = list(fixture.matches.all())
    return render(
        request,
        "core/fixture_detail.html",
        {
            "fixture": fixture,
            "singles": [m for m in matches if m.kind == Match.SINGLE],
            "doubles": [m for m in matches if m.kind == Match.DOUBLE],
            "outcome": fixture.result_for(settings.OUR_TEAM_NAME),
        },
    )


@login_required
def fixture_edit(request, pk):
    fixture = get_object_or_404(Fixture, pk=pk)
    queryset = fixture.matches.order_by("order")
    if request.method == "POST":
        form = FixtureForm(request.POST, instance=fixture)
        formset = MatchFormSet(request.POST, queryset=queryset)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, "Partita aggiornata. Classifica e statistiche sono già ricalcolate.")
            return redirect("fixture_detail", pk=fixture.pk)
    else:
        form = FixtureForm(instance=fixture)
        formset = MatchFormSet(queryset=queryset)
    return render(request, "core/fixture_edit.html", {"fixture": fixture, "form": form, "formset": formset})


@login_required
@require_POST
def fixture_delete(request, pk):
    fixture = get_object_or_404(Fixture, pk=pk)
    fixture.delete()
    messages.success(request, "Partita eliminata.")
    return redirect("fixture_list")


@login_required
def report_upload(request):
    ctx = {"text": "", "report": None, "exists": False}
    if request.method == "POST":
        text = request.POST.get("text", "")
        report = parse_report(text)
        ctx.update(text=text, report=report)
        if not report.errors:
            ctx["exists"] = Fixture.objects.filter(
                championship__name=report.championship, number=report.number
            ).exists()
            if request.POST.get("action") == "save":
                fixture, created = save_report(report)
                messages.success(
                    request, "Referto salvato." if created else "Referto salvato: la partita esistente è stata sostituita."
                )
                return redirect("fixture_detail", pk=fixture.pk)
    return render(request, "core/report_upload.html", ctx)
