# projects/urls.py

from django.urls import path
from .views import ProjectListCreateView, ProjectDetailView, ProjectStatsView

urlpatterns = [
    path("stats/", ProjectStatsView.as_view()),  # GET project statistics
    path("", ProjectListCreateView.as_view()),       # GET (list), POST (create)
    path("<int:pk>/", ProjectDetailView.as_view()),  # GET, PUT, DELETE
    
    
]