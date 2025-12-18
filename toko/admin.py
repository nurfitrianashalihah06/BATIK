# toko/admin.py
from django.contrib import admin
from .models import Produk, Kategori, Order, OrderItem, ContactMessage, Profile, RecommendationRule, Ulasan
from django.utils.html import format_html
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.urls import reverse

# --- 1. ADMIN KATEGORI ---
@admin.register(Kategori)
class KategoriAdmin(admin.ModelAdmin):
    # [TAMBAHAN] Masukkan 'tombol_aksi_hapus' ke list_display
    list_display = ['nama', 'slug', 'tombol_aksi_hapus']
    prepopulated_fields = {'slug': ('nama',)}

    # [TAMBAHAN] Fungsi Tombol Hapus
    def tombol_aksi_hapus(self, obj):
        url = reverse('admin:toko_kategori_delete', args=[obj.id])
        return format_html(
            '<a href="{}" style="background-color: #c44705; color: white; padding: 5px 10px; border-radius: 5px; text-decoration: none; font-weight: bold; font-size: 11px;">HAPUS</a>',
            url
        )
    tombol_aksi_hapus.short_description = "Aksi"
    tombol_aksi_hapus.allow_tags = True


# --- 2. ADMIN PRODUK ---
@admin.register(Produk)
class ProdukAdmin(admin.ModelAdmin):
    # [TAMBAHAN] Masukkan 'tombol_aksi_hapus' ke list_display
    list_display = ['nama', 'display_kategori', 'harga', 'stok', 'tersedia', 'tombol_aksi_hapus']
    list_filter = ['kategori', 'tersedia']
    list_editable = ['harga', 'stok', 'tersedia']
    prepopulated_fields = {'slug': ('nama',)}
    filter_horizontal = ('kategori',)

    @admin.display(description='Kategori Produk')
    def display_kategori(self, obj):
        return ", ".join([kat.nama for kat in obj.kategori.all()])

    # [TAMBAHAN] Fungsi Tombol Hapus
    def tombol_aksi_hapus(self, obj):
        url = reverse('admin:toko_produk_delete', args=[obj.id])
        return format_html(
            '<a href="{}" style="background-color: #c44705; color: white; padding: 5px 10px; border-radius: 5px; text-decoration: none; font-weight: bold; font-size: 11px;">HAPUS</a>',
            url
        )
    tombol_aksi_hapus.short_description = "Aksi"
    tombol_aksi_hapus.allow_tags = True


# --- 3. PENGATURAN USER & PROFILE (TETAP SAMA) ---
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profil Tambahan'
    fields = ('telepon', 'role')

class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)

try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass
admin.site.register(User, UserAdmin)

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['produk']
    extra = 0


# --- 4. ADMIN ORDER ---
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'user',
        'nama_depan',
        'nama_belakang',
        'total_bayar',
        'lunas',
        'lihat_bukti',
        'status_pengiriman',
        'nomor_resi',
        'dibuat',
        'tombol_aksi_hapus' # [PERBAIKAN] Ini wajib dimasukkan ke sini agar tombolnya muncul!
    ]
    list_filter = ('lunas', 'dibuat', 'status_pengiriman')
    search_fields = ['id', 'nama_depan', 'nama_belakang', 'email', 'nomor_resi']
    inlines = [OrderItemInline]
    list_editable = ('lunas', 'status_pengiriman', 'nomor_resi')

    actions = ['tandai_lunas']

    def tombol_aksi_hapus(self, obj):
        # Ini akan membuat tombol merah "Hapus" yang mengarah ke halaman konfirmasi hapus
        url = reverse('admin:toko_order_delete', args=[obj.id])
        return format_html(
            '<a href="{}" style="background-color: #c44705; color: white; padding: 5px 10px; border-radius: 5px; text-decoration: none; font-weight: bold; font-size: 11px;">HAPUS</a>',
            url
        )

    # Judul kolom di tabel
    tombol_aksi_hapus.short_description = "Aksi Cepat"
    tombol_aksi_hapus.allow_tags = True

    def lihat_bukti(self, obj):
        """Menampilkan thumbnail bukti pembayaran & link."""
        if obj.bukti_pembayaran:
            return format_html(
                '<a href="{0}" target="_blank"><img src="{0}" width="100" /></a>',
                obj.bukti_pembayaran.url
            )
        return "Belum di-upload"

    lihat_bukti.short_description = "Bukti Pembayaran"

    @admin.action(description='Tandai pesanan yang dipilih sebagai Lunas')
    def tandai_lunas(self, request, queryset):
        queryset.update(lunas=True)


# --- 5. ADMIN CONTACT MESSAGE ---
@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    # [TAMBAHAN] Tambahkan tombol hapus
    list_display = ('nama', 'email', 'subjek', 'dibuat', 'tombol_aksi_hapus')
    list_filter = ('dibuat',)
    search_fields = ('nama', 'email', 'subjek', 'pesan')
    readonly_fields = ('nama', 'email', 'subjek', 'pesan', 'dibuat')

    # [TAMBAHAN] Fungsi Tombol Hapus
    def tombol_aksi_hapus(self, obj):
        url = reverse('admin:toko_contactmessage_delete', args=[obj.id])
        return format_html(
            '<a href="{}" style="background-color: #c44705; color: white; padding: 5px 10px; border-radius: 5px; text-decoration: none; font-weight: bold; font-size: 11px;">HAPUS</a>',
            url
        )
    tombol_aksi_hapus.short_description = "Aksi"
    tombol_aksi_hapus.allow_tags = True


# --- 6. ADMIN RECOMMENDATION RULE ---
@admin.register(RecommendationRule)
class RecommendationRuleAdmin(admin.ModelAdmin):
    # [TAMBAHAN] Tambahkan tombol hapus
    list_display = ('antecedent', 'consequent', 'support', 'confidence', 'lift', 'tombol_aksi_hapus')

    # [TAMBAHAN] Fungsi Tombol Hapus
    def tombol_aksi_hapus(self, obj):
        url = reverse('admin:toko_recommendationrule_delete', args=[obj.id])
        return format_html(
            '<a href="{}" style="background-color: #c44705; color: white; padding: 5px 10px; border-radius: 5px; text-decoration: none; font-weight: bold; font-size: 11px;">HAPUS</a>',
            url
        )
    tombol_aksi_hapus.short_description = "Aksi"
    tombol_aksi_hapus.allow_tags = True


# --- 7. ADMIN ORDER ITEM ---
@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'produk', 'harga', 'jumlah')
    list_filter = ('order',)

@admin.register(Ulasan)
class UlasanAdmin(admin.ModelAdmin):
    list_display = ['user', 'produk', 'rating', 'dibuat']
    list_filter = ['rating', 'dibuat']