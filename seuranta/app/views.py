from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, get_object_or_404
from django.utils.timezone import now

from seuranta.models import Competition


@login_required
def own_competitions(request):
    user = request.user
    comps = Competition.objects.filter(publisher=user)
    return render(request,
                  'seuranta/own_competitions.html',
                  {'competitions': comps})


@login_required
def create_competition(request):
    return render(request,
                  'seuranta/create_competition.html')


@login_required
def edit_competition(request, competition_id):
    competition = get_object_or_404(Competition, id=competition_id)
    if competition.publisher != request.user:
        raise PermissionDenied
    return render(request,
                  'seuranta/edit_competition.html',
                  {'competition': competition})


@login_required
def edit_map(request, competition_id):
    competition = get_object_or_404(Competition, id=competition_id)
    if competition.publisher != request.user:
        raise PermissionDenied
    return render(request,
                  'seuranta/edit_map.html',
                  {'competition': competition})


@login_required
def edit_competitors(request, competition_id):
    competition = get_object_or_404(Competition, id=competition_id)
    if competition.publisher != request.user:
        raise PermissionDenied
    return render(request,
                  'seuranta/edit_competitors.html',
                  {'competition': competition})


def list_competitions(request):
    ts = now()
    qs = Competition.objects.all()
    live = qs.filter(
        start_date__lte=ts,
        end_date__gte=ts,
        publication_policy="public"
    ).order_by('start_date')
    upcoming = qs.filter(
        start_date__gt=ts,
        end_date__gt=ts,
        publication_policy="public"
    ).order_by('start_date')
    past = qs.filter(
        start_date__lt=ts,
        end_date__lt=ts,
        publication_policy="public"
    ).order_by('-end_date')
    return render(request,
                  'seuranta/list_competitions.html',
                  {'live': live, 'upcoming': upcoming, 'past': past})
