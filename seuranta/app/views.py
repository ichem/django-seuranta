from django.contrib.auth.decorators import login_required
from django.shortcuts import render

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