# toko/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.http import require_POST
from decimal import Decimal
from .models import Produk, Kategori, Order, OrderItem, Profile
from .forms import RegisterForm, OrderForm, BuktiPembayaranForm, ContactForm, UserUpdateForm, ProfileUpdateForm
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash


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
def detail_produk(request, produk_slug):
    produk = get_object_or_404(Produk, slug=produk_slug, tersedia=True)

    # Ambil produk terkait (opsional, tapi bagus untuk ada)
    produk_terkait = Produk.objects.filter(kategori__in=produk.kategori.all()).exclude(id=produk.id).distinct()[:4]

    context = {
        'produk': produk,
        'produk_terkait': produk_terkait,
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

@login_required # ✅ 3. Also protect the detail page view
def detail_produk(request, produk_slug):
    produk = get_object_or_404(Produk, slug=produk_slug, tersedia=True)
    context = {
        'produk': produk,
    }
    return render(request, 'toko/detail_produk.html', context)

def logout_view(request):
    logout(request)
    messages.success(request, 'Anda telah berhasil logout.')
    return redirect('toko:homepage')


@require_POST  # Memastikan view ini hanya bisa diakses via POST
def tambah_ke_keranjang(request, produk_id):
    # Ambil keranjang yang ada dari sesi, atau buat keranjang kosong
    keranjang = request.session.get('keranjang', {})

    # Ambil produk yang mau ditambahkan
    produk = get_object_or_404(Produk, id=produk_id)

    # Ambil jumlah dari form (defaultnya 1 jika tidak ada)
    # Kita pakai 'quantity' karena itu nama input di form detail produk
    jumlah = int(request.POST.get('quantity', 1))

    produk_id_str = str(produk_id)  # Gunakan string untuk kunci session

    if produk_id_str in keranjang:
        # Jika produk sudah ada di keranjang, tambahkan jumlahnya
        keranjang[produk_id_str]['jumlah'] += jumlah
    else:
        # Jika produk baru, tambahkan ke keranjang
        keranjang[produk_id_str] = {'jumlah': jumlah, 'harga': str(produk.harga)}

    # Simpan kembali keranjang ke dalam sesi
    request.session['keranjang'] = keranjang

    # Arahkan pengguna ke halaman keranjang
    return redirect('toko:lihat_keranjang')


@login_required
def lihat_keranjang(request):
    keranjang = request.session.get('keranjang', {})
    cart_items = []
    total_harga_keranjang = Decimal('0.00')

    for produk_id, item_data in keranjang.items():
        produk = get_object_or_404(Produk, id=int(produk_id))
        jumlah = item_data['jumlah']
        harga = Decimal(item_data['harga'])

        subtotal = harga * jumlah
        total_harga_keranjang += subtotal

        cart_items.append({
            'produk': produk,
            'jumlah': jumlah,
            'harga': harga,
            'subtotal': subtotal,
        })

    context = {
        'cart_items': cart_items,
        'total_harga_keranjang': total_harga_keranjang,
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
    if not keranjang:
        # Jika keranjang kosong, jangan biarkan checkout
        return redirect('toko:lihat_keranjang')

    # Hitung total harga dari sesi (untuk konfirmasi)
    total_harga_keranjang = Decimal('0.00')
    for item_data in keranjang.values():
        total_harga_keranjang += Decimal(item_data['harga']) * item_data['jumlah']

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            # 1. Simpan data alamat ke objek Order, tapi jangan ke database dulu
            order = form.save(commit=False)
            order.user = request.user
            order.total_bayar = total_harga_keranjang
            order.save()  # Simpan Order ke database

            # 2. Pindahkan item dari keranjang ke database OrderItem
            for produk_id, item_data in keranjang.items():
                produk = Produk.objects.get(id=int(produk_id))
                OrderItem.objects.create(
                    order=order,
                    produk=produk,
                    harga=Decimal(item_data['harga']),
                    jumlah=item_data['jumlah']
                )

            # 3. Bersihkan keranjang dari sesi
            request.session['keranjang'] = {}

            # 4. Arahkan ke halaman "Pesanan Berhasil" (akan kita buat nanti)
            # Untuk sekarang, kita arahkan ke homepage
            return redirect('toko:pesanan_berhasil', order_id=order.id)
    else:
        # Jika request GET, tampilkan form kosong
        form = OrderForm()

    context = {
        'form': form,
        'total_harga': total_harga_keranjang
    }
    return render(request, 'toko/checkout.html', context)

@login_required
def pesanan_berhasil(request, order_id):
    try:
        order = Order.objects.get(id=order_id, user=request.user)
    except Order.DoesNotExist:
        return redirect('toko:homepage')

    upload_form = BuktiPembayaranForm(instance=order) # Form untuk upload

    if request.method == 'POST':
        # Ini adalah proses upload bukti bayar
        upload_form = BuktiPembayaranForm(request.POST, request.FILES, instance=order)
        if upload_form.is_valid():
            upload_form.save()
            messages.success(request, 'Bukti pembayaran berhasil di-upload!')
            return redirect('toko:pesanan_berhasil', order_id=order.id) # Muat ulang halaman

    context = {
        'order': order,
        'upload_form': upload_form, # Kirim form ke template
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

@login_required # ✅ Halaman ini WAJIB login
def profil_view(request):
    orders = Order.objects.filter(user=request.user).order_by('-dibuat')

    # ✅ INI ADALAH KUNCI PERBAIKANNYA
    # Ambil profil, atau BUATKAN PROFIL BARU jika belum ada
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        # Gunakan 'profile' yang sudah kita ambil
        profile_form = ProfileUpdateForm(request.POST, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Profil Anda berhasil diperbarui.')
            return redirect('toko:profil')
        else:
            messages.error(request, 'Terjadi kesalahan. Periksa kembali data Anda.')
    else:
        # Tampilkan form yang sudah terisi
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=profile)

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'orders': orders,
    }
    return render(request, 'toko/profil.html', context)

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