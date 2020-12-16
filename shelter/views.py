from django.shortcuts import render
from django.http import HttpResponse

from shelter.models import *


def index(request):
    shelters = Shelter.objects.all()
    return render(request, 'main/index.html', locals())


def shelter(request, id):
    shelter = Shelter.objects.get(id=id)

    return render(request, 'main/shelter.html', locals())


def download_report(request, id):
    shelter = Shelter.objects.get(id=id)

    document = shelter.generate_report()
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    response['Content-Disposition'] = f'attachment; filename=registy.docx'
    document.save(response)

    return response
