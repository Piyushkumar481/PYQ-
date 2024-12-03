# uploads/urls.py
from django.urls import path
from . import views  # This imports views from the current app (uploads)

urlpatterns = [
    path('upload/', views.file_upload_view, name='file_upload'),
    path('upload/success/', views.upload_success_view, name='upload_success'),
]
