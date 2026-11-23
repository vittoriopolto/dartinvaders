from django.contrib import admin

from .models import Championship, Fixture, Match, Player, Team


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    search_fields = ["name"]


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ["name", "team", "tessera"]
    list_filter = ["team"]
    search_fields = ["name", "tessera"]


admin.site.register(Championship)


class MatchInline(admin.TabularInline):
    model = Match
    extra = 0


@admin.register(Fixture)
class FixtureAdmin(admin.ModelAdmin):
    list_display = ["__str__", "championship", "date"]
    inlines = [MatchInline]
