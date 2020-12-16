import inspect
from django.contrib import admin

from options import models

for model in inspect.getmembers(models):

    if model[0].startswith('Animal'):
        admin.site.register(model[1])
