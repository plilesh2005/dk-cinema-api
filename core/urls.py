from django.urls import path
from drive import views

urlpatterns = [
    path("api/folder/<str:folder_id>/", views.list_folder, name="list_folder"),
    path("api/root/", views.root_folder, name="root_folder"),
    path("api/file/<str:file_id>/", views.file_detail, name="file_detail"),
    path("api/stream/<str:file_id>/", views.stream_file, name="stream_file"),
    path("api/search/", views.search_videos, name="search_videos"),
    path("api/health/", views.health, name="health"),
]
