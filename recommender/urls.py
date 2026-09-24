from django.urls import path

from . import views

app_name = "recommender"

urlpatterns = [
    path("", views.home, name="home"),
    path("api/recommend", views.api_recommend, name="api_recommend"),
    path("api/search", views.api_search, name="api_search"),
    path("health", views.health, name="health"),
]
