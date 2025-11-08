# toko/urls.py
from django.urls import path
from . import views

app_name = 'toko'

urlpatterns = [
    # URL untuk homepage
    path('', views.homepage, name='homepage'),

    # URL untuk halaman daftar semua produk
    path('products/', views.daftar_produk, name='daftar_produk'),

    # URL untuk halaman detail produk
    path('products/<slug:produk_slug>/', views.detail_produk, name='detail_produk'),

    # URL untuk halaman tentang kami
    path('tentang-kami/', views.tentang_kami, name='tentang_kami'), # <-- Koma ditambahkan di sini

    # URL untuk halaman login
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),

    # ✅ TAMBAHKAN BARIS INI UNTUK LOGOUT
    path('logout/', views.logout_view, name='logout'),

    path('keranjang/tambah/<int:produk_id>/', views.tambah_ke_keranjang, name='tambah_ke_keranjang'),

    path('keranjang/', views.lihat_keranjang, name='lihat_keranjang'),

    path('checkout/', views.checkout_view, name='checkout'),

    path('pesanan-berhasil/<int:order_id>/', views.pesanan_berhasil, name='pesanan_berhasil'),

    path('kontak/', views.kontak_view, name='kontak'),

    path('profil/', views.profil_view, name='profil'),

    path('profil/ubah-password/', views.ubah_password_view, name='ubah_password'),

    path('keranjang/hapus/<int:produk_id>/', views.hapus_dari_keranjang, name='hapus_dari_keranjang'),
]