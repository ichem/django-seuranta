from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from seuranta.models import Competition


def admin_map_image(request, publisher, hash, pk):
    if request.user.is_anonymous() \
       or publisher != request.user.username:
        print request.user.username, publisher
        return HttpResponse(status=403)
    competition = get_object_or_404(Competition, pk=pk)
    response = competition.map.image_data
    mime = competition.map.format
    return HttpResponse(response, content_type=mime)
