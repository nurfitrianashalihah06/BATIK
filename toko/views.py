# toko/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.http import require_POST
from decimal import Decimal
from .models import Produk, Kategori, Order, OrderItem, Profile, RecommendationRule, Ulasan
from .forms import RegisterForm, OrderForm, BuktiPembayaranForm, ContactForm, UserUpdateForm, ProfileUpdateForm
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import render, redirect, get_object_or_404
from django.core.management import call_command
import midtransclient  # Library yang baru diinstall
from django.conf import settings
import time
from django.db.models import Avg
from .forms import UlasanForm
from django.db.models import Avg, Count, Q # Tambahkan Count dan Q



def homepage(request):
    # Ambil 4 produk terbaru yang tersedia
    produk_unggulan = Produk.objects.filter(tersedia=True).order_by('-dibuat')[:4]

    context = {
        'semua_produk': produk_unggulan
    }
    return render(request, 'toko/homepage.html', context)

def daftar_produk(request):
    semua_produk = Produk.objects.filter(tersedia=True)
    semua_kategori = Kategori.objects.all()
    context = {
        'semua_produk': semua_produk,
        'semua_kategori': semua_kategori,
    }
    return render(request, 'toko/daftar_produk.html', context)


@login_required  # ✅ 2. TAMBAHKAN BARIS INI
def detail_produk(request, slug):
    produk = get_object_or_404(Produk, slug=slug)

    # 1. Handle Form Ulasan (Jika User Submit)
    if request.method == 'POST' and request.user.is_authenticated:
        form = UlasanForm(request.POST)
        if form.is_valid():
            ulasan = form.save(commit=False)
            ulasan.produk = produk
            ulasan.user = request.user
            ulasan.save()
            messages.success(request, "Terima kasih! Ulasan Anda telah berhasil dikirim.")
            return redirect('toko:detail_produk', slug=slug)
    else:
        form = UlasanForm()

    # 2. Ambil Semua Ulasan & Hitung Rata-rata
    ulasan_list = produk.ulasan.all().order_by('-dibuat')
    avg_rating = ulasan_list.aggregate(Avg('rating'))['rating__avg'] or 0

    # Rekomendasi (Kode yang sebelumnya sudah ada)
    rekomendasi_rules = RecommendationRule.objects.filter(antecedent=produk).order_by('-lift')[:4]
    rekomendasi_produk = [rule.consequent for rule in rekomendasi_rules]

    if not rekomendasi_produk:
        rekomendasi_produk = Produk.objects.filter(kategori__in=produk.kategori.all()).exclude(id=produk.id).order_by(
            '?')[:4]

    context = {
        'produk': produk,
        'rekomendasi': rekomendasi_produk,
        'ulasan_list': ulasan_list,
        'avg_rating': round(avg_rating, 1),  # Dibulatkan 1 desimal
        'form_ulasan': form,
        'range_bintang': range(1, 6),  # Untuk loop bintang di HTML
    }
    return render(request, 'toko/detail_produk.html', context)

def login_view(request):
    if request.method == 'POST':
        # Ambil data dari form
        username_dari_form = request.POST.get('username')
        password_dari_form = request.POST.get('password')

        # Autentikasi pengguna
        user = authenticate(request, username=username_dari_form, password=password_dari_form)

        if user is not None:
            # Jika user ada dan password benar
            login(request, user)

            next_url = request.POST.get('next')
            if next_url:
                return redirect(next_url)
            else:
                return redirect('toko:homepage')
        else:
            # Jika user tidak ada atau password salah
            messages.warning(request, 'Username atau password salah. Silakan coba lagi.')

    # Tampilkan halaman login (jika GET atau jika login gagal)
    return render(request, 'toko/login.html')


# toko/views.py
# ✅ GUNAKAN FUNGSI YANG LEBIH BAIK INI
def register_view(request):
    if request.method == 'POST':
        # 1. Gunakan RegisterForm untuk data POST
        form = RegisterForm(request.POST)
        if form.is_valid():
            # 2. Jika form valid, simpan data ke database
            #    (forms.py akan menangani username=email dan hashing password)
            form.save()
            messages.success(request, 'Akun Anda berhasil dibuat! Silakan login.')
            return redirect('toko:login')
        else:
            # 3. Jika tidak valid, kirim pesan error
            messages.error(request, 'Terjadi kesalahan. Periksa kembali data Anda.')
    else:
        # 4. Jika bukan POST, tampilkan form kosong
        form = RegisterForm()

    # 5. Kirim 'form' ke template (baik yang kosong atau yang ada errornya)
    return render(request, 'toko/register.html', {'form': form})

def tentang_kami(request):
    return render(request, 'toko/tentang_kami.html')

@login_required # ✅ 2. Add this decorator above the view
def daftar_produk(request):
    semua_produk = Produk.objects.filter(tersedia=True).order_by('-dibuat')
    context = {
        'semua_produk': semua_produk,
    }

    return render(request, 'toko/daftar_produk.html', context)


def detail_produk(request, produk_slug):
    produk = get_object_or_404(Produk, slug=produk_slug)

    # LOGIKA REKOMENDASI:
    # "Ambil semua aturan di mana produk ini adalah pemicu (antecedent)"
    # Urutkan berdasarkan 'lift' (kualitas hubungan) atau 'confidence' (kepastian) tertinggi
    rekomendasi_rules = RecommendationRule.objects.filter(
        antecedent=produk
    ).order_by('-lift')[:4]  # Ambil 4 teratas saja

    # Ambil produk aslinya dari rules tersebut
    rekomendasi_produk = [rule.consequent for rule in rekomendasi_rules]

    context = {
        'produk': produk,
        'rekomendasi': rekomendasi_produk,  # Kirim ke template
    }

    # --- BAGIAN 2: TAMBAHAN LOGIKA ULASAN (DI BAWAHNYA) ---

    # A. Handle Form Submission (Jika tombol diklik)
    if request.method == 'POST':
        if request.user.is_authenticated:
            form = UlasanForm(request.POST)
            if form.is_valid():
                # Cek apakah user sudah pernah ulas? (Opsional, hapus if ini jika boleh ulas berkali-kali)
                if Ulasan.objects.filter(user=request.user, produk=produk).exists():
                    messages.warning(request, "Anda sudah pernah mengulas produk ini.")
                else:
                    ulasan = form.save(commit=False)
                    ulasan.produk = produk
                    ulasan.user = request.user
                    ulasan.save()
                    messages.success(request, "Ulasan berhasil dikirim!")

                # Redirect menggunakan 'produk_slug' agar sesuai dengan urls.py Anda
                return redirect('toko:detail_produk', produk_slug=produk_slug)
            else:
                messages.error(request, "Gagal! Pastikan rating dipilih.")
        else:
            return redirect('login')
    else:
        form = UlasanForm()

    # B. Ambil Data Ulasan untuk Ditampilkan
    ulasan_list = produk.ulasan.all().order_by('-dibuat')
    avg_rating = ulasan_list.aggregate(Avg('rating'))['rating__avg'] or 0

    # --- BAGIAN 3: GABUNGKAN DATA KE CONTEXT ---
    context = {
        'produk': produk,
        'rekomendasi': rekomendasi_produk,  # Dari kode asli Anda

        # Tambahan Data Ulasan:
        'ulasan_list': ulasan_list,
        'avg_rating': round(avg_rating, 1),
        'form': form,  # Penting untuk menampilkan form bintang
    }
    return render(request, 'toko/detail_produk.html', context)

def logout_view(request):
    logout(request)
    messages.success(request, 'Anda telah berhasil logout.')
    return redirect('toko:homepage')


# --- FUNGSI TAMBAH KERANJANG ---
@login_required(login_url='login')
def tambah_ke_keranjang(request, produk_id):
    # 1. Ambil keranjang, default kosong
    keranjang = request.session.get('keranjang', {})

    # 2. Ambil Produk & Input Jumlah
    produk = get_object_or_404(Produk, id=produk_id)
    try:
        jumlah_minta = int(request.POST.get('quantity', 1))
        if jumlah_minta < 1: jumlah_minta = 1
    except ValueError:
        jumlah_minta = 1

    str_id = str(produk_id)

    # 3. LOGIKA PENYIMPANAN (Dengan fitur Reset Otomatis)
    try:
        if produk.stok >= jumlah_minta:
            # Cek dulu: apakah data di keranjang formatnya benar (angka)?
            # Kalau ada data lama yang formatnya 'dict' atau aneh, ini bakal error
            current_qty = keranjang.get(str_id, 0)

            # Paksa jadi int biar aman
            if not isinstance(current_qty, int):
                current_qty = 0

            keranjang[str_id] = current_qty + jumlah_minta

            # Simpan
            request.session['keranjang'] = keranjang
            request.session.modified = True
            messages.success(request, f"Berhasil menambahkan {jumlah_minta} {produk.nama} ke keranjang.")
        else:
            messages.error(request, f"Stok kurang! Sisa: {produk.stok}")

    except Exception as e:
        # ⚠️ KALAU ERROR (Misal karena data lama rusak), KITA RESET KERANJANGNYA
        request.session['keranjang'] = {}
        request.session[str_id] = jumlah_minta
        request.session.modified = True
        messages.warning(request,
                         "Keranjang di-reset karena format lama tidak kompatibel. Produk berhasil ditambahkan.")

    return redirect('toko:lihat_keranjang')


# D:\TA\BATIK\toko\views.py

@login_required(login_url='toko:login')
def lihat_keranjang(request):
    keranjang = request.session.get('keranjang', {})
    cart_items = []
    total_tagihan = Decimal('0.00')

    # Simpan ID produk yang ada di keranjang untuk filter rekomendasi
    cart_product_ids = []

    # 1. Proses Data Keranjang
    list_id = list(keranjang.keys())
    for produk_id in list_id:
        data = keranjang[produk_id]
        try:
            if isinstance(data, int):
                jumlah = data
            else:
                jumlah = int(data.get('jumlah', 1))

            produk = Produk.objects.get(id=int(produk_id))
            subtotal = produk.harga * jumlah
            total_tagihan += subtotal

            cart_items.append({
                'produk': produk,
                'jumlah': jumlah,
                'subtotal': subtotal,
                'harga': produk.harga
            })

            cart_product_ids.append(produk.id)

        except (Produk.DoesNotExist, ValueError, TypeError):
            del keranjang[produk_id]
            request.session.modified = True

    # 2. LOGIKA REKOMENDASI DI KERANJANG
    rekomendasi_list = []

    if cart_product_ids:
        rules = RecommendationRule.objects.filter(
            antecedent__id__in=cart_product_ids
        ).order_by('-lift')

        seen_ids = set(cart_product_ids)

        for rule in rules:
            produk_rek = rule.consequent
            if produk_rek.id not in seen_ids:
                rekomendasi_list.append(produk_rek)
                seen_ids.add(produk_rek.id)

            if len(rekomendasi_list) >= 4:
                break

    context = {
        'cart_items': cart_items,
        'total_tagihan': total_tagihan,
        'total_harga_keranjang': total_tagihan,
        # --- PERUBAHAN DI SINI ---
        # Kita ganti namanya jadi 'rekomendasi_cart' supaya tidak nyangkut di footer global
        'rekomendasi_cart': rekomendasi_list,
    }
    return render(request, 'toko/keranjang.html', context)

@login_required  # Pastikan hanya user yang login yang bisa hapus
def hapus_dari_keranjang(request, produk_id):
    # Ambil keranjang dari sesi
    keranjang = request.session.get('keranjang', {})

    # Ubah ID produk menjadi string (karena kunci di sesi adalah string)
    produk_id_str = str(produk_id)

    if produk_id_str in keranjang:
        # Hapus item dari dictionary keranjang
        del keranjang[produk_id_str]

        # Simpan kembali keranjang yang sudah diperbarui ke sesi
        request.session['keranjang'] = keranjang
        messages.success(request, 'Produk berhasil dihapus dari keranjang.')

    # Arahkan pengguna kembali ke halaman keranjang
    return redirect('toko:lihat_keranjang')

@login_required  # Pastikan checkout juga dilindungi
def checkout_view(request):
    keranjang = request.session.get('keranjang', {})

    # Jika keranjang kosong, lempar balik
    if not keranjang:
        messages.warning(request, "Keranjang belanja Anda kosong.")
        return redirect('toko:daftar_produk')

    total_tagihan = Decimal('0.00')
    items_checkout = []

    # 1. HITUNG TOTAL BARANG (MURNI)
    for produk_id, data in keranjang.items():
        try:
            if isinstance(data, int):
                jumlah = data
            else:
                jumlah = int(data.get('jumlah', 1))

            produk = Produk.objects.get(id=int(produk_id))
            subtotal = produk.harga * jumlah
            total_tagihan += subtotal

            items_checkout.append({
                'produk': produk,
                'jumlah': jumlah,
                'harga': produk.harga,
                'subtotal': subtotal
            })

        except (Produk.DoesNotExist, ValueError):
            continue

    # --- BAGIAN POST (SAAT KLIK TOMBOL BUAT PESANAN) ---
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            # 1. Tangkap Ongkir dari Input Hidden di HTML
            try:
                # Ambil nilai 'input_ongkir', kalau tidak ada anggap 0
                nilai_ongkir = int(request.POST.get('input_ongkir', 0))
            except ValueError:
                nilai_ongkir = 0

            # 2. Simpan Header Order
            order = form.save(commit=False)
            order.user = request.user

            # 3. MASUKKAN ONGKIR KE DATABASE
            order.ongkir = nilai_ongkir

            # 4. UPDATE TOTAL BAYAR (PENTING: Barang + Ongkir)
            # Ini yang bikin Midtrans nanti harganya benar
            order.total_bayar = total_tagihan + Decimal(nilai_ongkir)

            order.save()

            # 5. Simpan Item Order
            for item in items_checkout:
                OrderItem.objects.create(
                    order=order,
                    produk=item['produk'],
                    harga=item['harga'],
                    jumlah=item['jumlah']
                )

            # Update Rekomendasi (Opsional)
            try:
                pass
                # call_command('generate_rules')
            except Exception:
                pass

            # 6. Reset Keranjang & Redirect ke Bayar
            request.session['keranjang'] = {}
            messages.success(request, "Pesanan berhasil dibuat!")
            return redirect('toko:pesanan_berhasil', order_id=order.id)

    else:
        form = OrderForm()

    context = {
        'form': form,
        'total_harga': total_tagihan,  # Ini dikirim ke Javascript sebagai subtotal
        'daftar_belanja': items_checkout
    }
    return render(request, 'toko/checkout.html', context)

@login_required
def pesanan_berhasil(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    # 1. Konfigurasi Midtrans Snap
    snap = midtransclient.Snap(
        is_production=settings.MIDTRANS_IS_PRODUCTION,
        server_key=settings.MIDTRANS_SERVER_KEY,
        client_key=settings.MIDTRANS_CLIENT_KEY
    )

    # 2. Buat ID Unik untuk Midtrans
    # Format: ORDER-[ID]-[TIMESTAMP] (Contoh: ORDER-15-1762312)
    # Gunanya supaya kalau user batal bayar lalu bayar lagi, ID-nya beda & tidak ditolak Midtrans
    timestamp = int(time.time())
    order_id_midtrans = f"ORDER-{order.id}-{timestamp}"

    # 3. Siapkan Data Transaksi
    param = {
        "transaction_details": {
            "order_id": order_id_midtrans,
            "gross_amount": int(order.total_bayar),
        },
        "customer_details": {
            # KITA PAKSA DATA DUMMY BIAR GAK ERROR 400
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",  # <-- INI KUNCINYA (Jangan ambil dari request.user dulu)
            "phone": "08123456789",
        },
        "callbacks": {
            "finish": "http://127.0.0.1:8000/profil/"
        }
    }

    # 4. Minta Token ke Midtrans
    snap_token = None
    try:
        snap_response = snap.create_transaction(param)
        snap_token = snap_response['token']
        print(f"✅ SUKSES! Token didapat: {snap_token}")  # CCTV SUKSES

    except Exception as e:
        # CCTV ERROR - INI YANG KITA CARI
        print("\n" + "=" * 50)
        print("❌ ERROR MIDTRANS TERDETEKSI!")
        print(f"Pesan Error: {e}")
        print("-" * 20)
        print(f"Server Key yang dipakai: {settings.MIDTRANS_SERVER_KEY}")
        print(f"Client Key yang dipakai: {settings.MIDTRANS_CLIENT_KEY}")
        print("=" * 50 + "\n")

    # Handle Upload Bukti Bayar Manual (Cadangan)
    upload_form = BuktiPembayaranForm(instance=order)
    if request.method == 'POST':
        upload_form = BuktiPembayaranForm(request.POST, request.FILES, instance=order)
        if upload_form.is_valid():
            upload_form.save()
            messages.success(request, 'Bukti bayar terupload!')
            return redirect('toko:pesanan_berhasil', order_id=order.id)

    context = {
        'order': order,
        'upload_form': upload_form,
        'snap_token': snap_token,  # Token buat pop-up
        'client_key': settings.MIDTRANS_CLIENT_KEY,  # Kunci Client buat HTML
    }
    return render(request, 'toko/pesanan_berhasil.html', context)

def kontak_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save() # Simpan pesan ke database
            messages.success(request, 'Pesan Anda telah terkirim! Kami akan segera merespons.')
            return redirect('toko:kontak') # Arahkan kembali ke halaman kontak
    else:
        form = ContactForm() # Tampilkan form kosong

    return render(request, 'toko/kontak.html', {'form': form})


# D:\TA\BATIK\toko\views.py

@login_required
def profil_view(request):
    # === LOGIKA TANGKAP HASIL BAYAR (VERSI DEBUGGING) ===

    # 1. Ambil data dari URL
    status_midtrans = request.GET.get('transaction_status')
    order_id_midtrans = request.GET.get('order_id')
    status_code = request.GET.get('status_code')

    # 2. CETAK DI TERMINAL
    if order_id_midtrans:
        print(f"\n[DEBUG MIDTRANS] User kembali dari pembayaran!")
        print(f"Order ID: {order_id_midtrans}")
        print(f"Status: {status_midtrans}")
        print(f"Code: {status_code}")

    # 3. Logika Update Status
    if order_id_midtrans:
        if status_midtrans in ['settlement', 'capture'] or status_code == '200':
            try:
                parts = order_id_midtrans.split('-')
                if len(parts) >= 2:
                    real_order_id = parts[1]
                    order_update = Order.objects.get(id=int(real_order_id))

                    if not order_update.lunas:
                        order_update.lunas = True
                        order_update.save()
                        print(f"✅ SUKSES! Order #{real_order_id} diubah jadi LUNAS.")
                        messages.success(request, f"Pembayaran Pesanan #{real_order_id} BERHASIL!")
                    else:
                        print(f"ℹ️ Order #{real_order_id} sudah lunas sebelumnya.")

            except Exception as e:
                print(f"❌ ERROR SAAT UPDATE: {e}")

    # === [BARU] LOGIKA HAPUS RIWAYAT LAMA (MAX 5) ===
    # 1. Cek semua pesanan user ini
    semua_pesanan = Order.objects.filter(user=request.user).order_by('-dibuat')

    # 2. Jika lebih dari 5, hapus sisanya
    if semua_pesanan.count() > 3:
        # Ambil 5 ID pesanan TERBARU untuk diselamatkan
        id_disimpan = list(semua_pesanan[:3].values_list('id', flat=True))

        # Hapus pesanan yang ID-nya TIDAK ADA dalam daftar yang diselamatkan
        Order.objects.filter(user=request.user).exclude(id__in=id_disimpan).delete()
        print(f"🧹 Membersihkan riwayat pesanan lama (Menyisakan 3 terbaru).")
    # ================================================

    # ... (Kode form profil di bawah ini SAMA SEPERTI BIASA) ...
    profile, created = Profile.objects.get_or_create(user=request.user)

    # Ambil ulang orders (sekarang pasti jumlahnya maksimal 5)
    orders = Order.objects.filter(user=request.user).order_by('-dibuat')

    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'Profil berhasil diupdate.')
            return redirect('toko:profil')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=profile)

    return render(request, 'toko/profil.html', {
        'user_form': u_form, 'profile_form': p_form, 'orders': orders
    })

@login_required # Pastikan user sudah login
def ubah_password_view(request):
    if request.method == 'POST':
        # Gunakan PasswordChangeForm, berikan data user dan data POST
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save() # Simpan password baru
            # PENTING! Update sesi user agar tidak ter-logout
            update_session_auth_hash(request, user)
            messages.success(request, 'Kata sandi Anda berhasil diperbarui.')
            return redirect('toko:profil') # Arahkan kembali ke halaman profil
        else:
            messages.error(request, 'Terjadi kesalahan. Periksa kembali form Anda.')
    else:
        # Tampilkan form kosong
        form = PasswordChangeForm(user=request.user)

    return render(request, 'toko/ubah_password.html', {'form': form})


@user_passes_test(lambda u: u.is_superuser)
def update_rekomendasi(request):
    try:
        # Memanggil file generate_rules.py lewat kode
        call_command('generate_rules')
        messages.success(request, "Sukses! Rekomendasi berhasil diperbarui.")
    except Exception as e:
        messages.error(request, f"Gagal update: {str(e)}")

    return redirect('toko:homepage')

