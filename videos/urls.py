from django.urls import path
from .views import upload_view, search_subtitles

urlpatterns = [
    path('upload/', upload_view, name='upload'),
    path('search/', search_subtitles, name='search_subtitles'),
]
