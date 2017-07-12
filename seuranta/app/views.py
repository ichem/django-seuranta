from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, get_object_or_404

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
