# ECommerceBatik/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # Arahkan semua request ke root URL ke aplikasi 'toko'
    path('', include('toko.urls')),
]

# Ini penting untuk menampilkan gambar produk saat development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    # Jika Anda juga menggunakan file media (upload gambar oleh user)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)