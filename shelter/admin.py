from django.contrib import admin

from shelter.models import Shelter, ShelterStaff, Company

admin.site.register(Company)
admin.site.register(Shelter)
admin.site.register(ShelterStaff)
