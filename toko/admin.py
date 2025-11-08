# toko/admin.py
from django.contrib import admin
from .models import Kategori, Produk
from .models import Produk, Kategori, Order, OrderItem, ContactMessage


@admin.register(Kategori)
class KategoriAdmin(admin.ModelAdmin):
    list_display = ['nama', 'slug']
    prepopulated_fields = {'slug': ('nama',)}


@admin.register(Produk)
class ProdukAdmin(admin.ModelAdmin):
    # 1. Ganti 'kategori' dengan nama fungsi baru 'display_kategori'
    list_display = ['nama', 'display_kategori', 'harga', 'stok', 'tersedia']

    list_filter = ['kategori', 'tersedia']
    list_editable = ['harga', 'stok', 'tersedia']
    prepopulated_fields = {'slug': ('nama',)}
    filter_horizontal = ('kategori',)

    # 2. Tambahkan fungsi ini untuk menampilkan semua kategori
    @admin.display(description='Kategori Produk')
    def display_kategori(self, obj):
        return ", ".join([kat.nama for kat in obj.kategori.all()])

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('nama', 'email', 'subjek', 'dibuat')
    list_filter = ('dibuat',)
    search_fields = ('nama', 'email', 'subjek', 'pesan')
    readonly_fields = ('nama', 'email', 'subjek', 'pesan', 'dibuat')

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['produk']
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'nama_depan', 'email', 'total_bayar', 'lunas', 'dibuat']
    list_filter = ['lunas', 'dibuat']
    inlines = [OrderItemInline]
    search_fields = ['id', 'nama_depan', 'email']