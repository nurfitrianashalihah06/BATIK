# toko/forms.py
from django import forms
from .models import Order, ContactMessage
from django.contrib.auth.models import User
from .models import Profile

# ✅ TAMBAHKAN FORM INI
class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        # Tampilkan field yang perlu diisi pengguna
        fields = ['nama_depan', 'nama_belakang', 'email', 'telepon', 'alamat', 'kota', 'kode_pos']

        # Atur placeholder agar terlihat rapi (opsional)
        widgets = {
            'nama_depan': forms.TextInput(attrs={'placeholder': 'Nama Depan'}),
            'nama_belakang': forms.TextInput(attrs={'placeholder': 'Nama Belakang'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Email Anda'}),
            'telepon': forms.TextInput(attrs={'placeholder': 'Nomor Telepon'}),
            'alamat': forms.TextInput(attrs={'placeholder': 'Alamat Lengkap Jalan'}),
            'kota': forms.TextInput(attrs={'placeholder': 'Kota/Kabupaten'}),
            'kode_pos': forms.TextInput(attrs={'placeholder': 'Kode Pos'}),
        }


class RegisterForm(forms.ModelForm):
    # Field kustom yang tidak ada di model User standar
    phone = forms.CharField(
        label="Nomor Telepon",
        max_length=15,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Masukkan Nomor Telepon',
            'autocomplete': 'tel',
            'type': 'tel'
        })
    )

    password = forms.CharField(
        label="Kata Sandi",
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Masukkan Kata Sandi',
            'autocomplete': 'new-password'
        })
    )

    password_confirm = forms.CharField(
        label="Konfirmasi Kata Sandi",
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Konfirmasi Kata Sandi',
            'autocomplete': 'new-password'
        })
    )

    register_as = forms.ChoiceField(
        label="Register Sebagai",
        choices=[
            ("", "Register Sebagai"),  # Pilihan placeholder
            ("customer", "Customer"),
            ("seller", "Seller"),
        ],
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-control',
        })
    )

    class Meta:
        model = User
        # Daftar field yang kita ambil dari model User
        fields = ['first_name', 'username', 'email']
        labels = {
            'first_name': 'Nama Lengkap',
            'username': 'Username',
            'email': 'Alamat Email',
        }
        # Tambahkan widget di sini untuk placeholder
        widgets = {
            'first_name': forms.TextInput(attrs={
                'placeholder': 'Masukkan Nama',
                'autocomplete': 'name'
            }),
            'username': forms.TextInput(attrs={
                'placeholder': 'Buat Username (contoh: budi_keren)',
                'autocomplete': 'username'
            }),
            'email': forms.EmailInput(attrs={
                'placeholder': 'Masukkan Email',
                'autocomplete': 'email'
            }),
        }

    # Validasi untuk email unik
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email ini sudah terdaftar.")
        return email

    # Validasi untuk username unik
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Username ini sudah terpakai.")
        return username

    # Validasi untuk password cocok
    def clean_password_confirm(self):
        password = self.cleaned_data.get('password')
        password_confirm = self.cleaned_data.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("Konfirmasi kata sandi tidak cocok.")
        return password_confirm

    # Override metode save
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()

        # Ambil data kustom dari form
        telepon = self.cleaned_data.get('phone')
        role = self.cleaned_data.get('register_as')

        # Buat dan simpan Profile yang terhubung dengan User
        Profile.objects.create(
            user=user,
            telepon=telepon,
            role=role
        )

        return user

class BuktiPembayaranForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['bukti_pembayaran']
        labels = {
            'bukti_pembayaran': 'Upload Bukti Pembayaran'
        }

class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['nama', 'email', 'subjek', 'pesan']
        widgets = {
            'nama': forms.TextInput(attrs={'placeholder': 'Nama Lengkap Anda'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Email Anda'}),
            'subjek': forms.TextInput(attrs={'placeholder': 'Subjek Pesan'}),
            'pesan': forms.Textarea(attrs={'placeholder': 'Tulis pesan Anda di sini...', 'rows': 5}),
        }

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        # Tentukan field yang boleh di-edit
        fields = ['first_name', 'email']
        labels = {
            'first_name': 'Nama Lengkap',
        }
        widgets = {
            'first_name': forms.TextInput(attrs={'placeholder': 'Masukkan Nama Lengkap Anda'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Masukkan Email Anda'}),
        }

    def clean_email(self):
        """Validasi jika email diubah ke email yang sudah ada."""
        email = self.cleaned_data.get('email')
        # Cek apakah email berubah DAN email baru sudah dipakai user lain
        if email and User.objects.filter(email=email).exclude(username=self.instance.username).exists():
            raise forms.ValidationError('Email ini sudah digunakan oleh akun lain.')
        return email


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['telepon']
        labels = {
            'telepon': 'Nomor Telepon',
        }
        widgets = {
            'telepon': forms.TextInput(attrs={'placeholder': 'Masukkan Nomor Telepon Anda'}),
        }