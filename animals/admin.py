from django.contrib import admin

from animals.models import *

admin.site.register(Animal)
admin.site.register(AnimalVacine)
admin.site.register(AnimalDrug)
admin.site.register(AnimalCapture)
admin.site.register(AnimalInspection)
admin.site.register(AnimalInShelter)
admin.site.register(OwnerEntity)
admin.site.register(OwnerIndividual)
admin.site.register(AnimalRequest)
