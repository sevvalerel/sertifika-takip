from django.urls import path

from certificates import views

urlpatterns = [
    path("", views.certificate_list, name="certificate_list"),
]
