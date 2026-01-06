from django.urls import path
from .views import file_list_view, upload_view, download_view, landing_view, dashboard_view

urlpatterns = [
    path('', landing_view, name='landing'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('files/', file_list_view, name='file_list'),
    path('upload/', upload_view, name='upload'),
    path('file/<int:pk>/download/', download_view, name='download'),
]
