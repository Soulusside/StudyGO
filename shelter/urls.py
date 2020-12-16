from django.urls import path, include

from shelter import views


urlpatterns = [
    path('', views.index),
    path('shelter/<int:id>', views.shelter, name='shelter'),
    path('download_report/<int:id>', views.download_report, name='download_report'),
]
