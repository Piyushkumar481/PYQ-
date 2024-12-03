# file_upload/urls.py
from django.contrib import admin
from django.urls import path, include  # include is used for app URLs

urlpatterns = [
    path('admin/', admin.site.urls),
    path('uploads/', include('uploads.urls')),  # This includes your app's URLs
]
