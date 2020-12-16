from django.urls import path, include

from animals import views


urlpatterns = [
    path('refresh_from_csv/', views.refresh_from_csv),
    path('download_card/<int:id>', views.download_card, name='download_card'),
]
