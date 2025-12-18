# toko/models.py
from django.urls import reverse

from django.db import models
from django.contrib.auth.models import User

class Kategori(models.Model):
    nama = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = "Kategori"

    def __str__(self):
        return self.nama

class Produk(models.Model):
    kategori = models.ManyToManyField(Kategori, related_name='produk')
    nama = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    gambar = models.ImageField(upload_to='produk_gambar/', blank=True)
    deskripsi = models.TextField(blank=True)
    harga = models.DecimalField(max_digits=10, decimal_places=2)
    stok = models.PositiveIntegerField()
    tersedia = models.BooleanField(default=True)
    dibuat = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-dibuat',) # Urutkan dari yang terbaru
        verbose_name_plural = "Produk"

    def __str__(self):
        return self.nama

    def get_absolute_url(self):
        return reverse('toko:detail_produk', args=[self.slug])


class Order(models.Model):
    STATUS_PENGIRIMAN_CHOICES = [
        ('pending', 'Menunggu Diproses'),
        ('dikirim', 'Telah Dikirim'),
        ('selesai', 'Selesai'),
        ('dibatalkan', 'Dibatalkan'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    nama_depan = models.CharField(max_length=100)
    nama_belakang = models.CharField(max_length=100)
    email = models.EmailField()
    telepon = models.CharField(max_length=20)
    alamat = models.CharField(max_length=255)
    kota = models.CharField(max_length=100)
    kode_pos = models.CharField(max_length=10)
    dibuat = models.DateTimeField(auto_now_add=True)

    status_pengiriman = models.CharField(
        max_length=20,
        choices=STATUS_PENGIRIMAN_CHOICES,
        default='pending'
    )
    nomor_resi = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        ordering = ('-dibuat',)

    def __str__(self):
        return f'Pesanan {self.id}'

    total_bayar = models.DecimalField(max_digits=10, decimal_places=2)
    lunas = models.BooleanField(default=False)
    total_bayar = models.DecimalField(max_digits=10, decimal_places=2)
    lunas = models.BooleanField(default=False)

    class Meta:
        ordering = ('-dibuat',)

    def __str__(self):
        return f'Pesanan {self.id}'

    bukti_pembayaran = models.ImageField(upload_to='bukti_pembayaran/', null=True, blank=True)

    class Meta:
        ordering = ('-dibuat',)

    def __str__(self):
        return f'Pesanan {self.id}'

    kota = models.CharField(max_length=100)

    # TAMBAHAN BARU:
    ongkir = models.DecimalField(max_digits=10, decimal_places=2, default=0)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    produk = models.ForeignKey(Produk, related_name='order_items', on_delete=models.CASCADE)
    harga = models.DecimalField(max_digits=10, decimal_places=2)
    jumlah = models.PositiveIntegerField(default=1)

    def __str__(self):
        return str(self.id)

class ContactMessage(models.Model):
    nama = models.CharField(max_length=100)
    email = models.EmailField()
    subjek = models.CharField(max_length=200)
    pesan = models.TextField()
    dibuat = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-dibuat',)

    def __str__(self):
        return f'Pesan dari {self.nama} ({self.subjek})'

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    telepon = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=20, default='customer')

    def __str__(self):
        return f'{self.user.username} Profile'


class RecommendationRule(models.Model):
    # Produk A (Jika beli ini...)
    antecedent = models.ForeignKey(Produk, related_name='antecedent_rules', on_delete=models.CASCADE)

    # Produk B (...Maka direkomendasikan ini)
    consequent = models.ForeignKey(Produk, related_name='consequent_rules', on_delete=models.CASCADE)

    # Metrik dari Algoritma Apriori
    support = models.DecimalField(max_digits=6, decimal_places=4, default=0)  # Seberapa sering muncul
    confidence = models.DecimalField(max_digits=6, decimal_places=4, default=0)  # Seberapa kuat hubungannya
    lift = models.DecimalField(max_digits=6, decimal_places=4, default=0)  # Seberapa valid aturannya (>1 itu bagus)

    def __str__(self):
        return f"{self.antecedent} -> {self.consequent} (Lift: {self.lift})"

class Ulasan(models.Model):
    produk = models.ForeignKey(Produk, related_name='ulasan', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(default=5) # Angka 1 sampai 5
    komentar = models.TextField(blank=True, null=True)
    dibuat = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.produk.nama}"