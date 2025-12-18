import pandas as pd
from django.core.management.base import BaseCommand
from toko.models import Produk, RecommendationRule, Kategori
from itertools import combinations
from collections import Counter
import os


class Command(BaseCommand):
    help = 'Generate Rules Dua Arah (Bolak-Balik)'

    def handle(self, *args, **kwargs):
        # --- MAPPING AREA ---
        MAPPING_KATEGORI = {
            'Batik Cap': 'Batik Cap',
            'Batik Modern': 'Batik Modern',
            'Batik Ciprat': 'Batik Ciprat',
            'Batik Tulis Wonogiren': 'Batik Tulis Wonogiren',
            'Kain Mentahan': 'Kain Mentahan',
            'Batik Tulis Warna Alam': 'Warna Alam',  # Sesuaikan nama Admin
            'Batik Tulis Sogan': 'Batik Tulis Sogan',  # Pastikan ada di Admin
            'Kain Polos': 'Kain Polos',  # Pastikan ada di Admin
        }
        # --------------------

        file_path = 'transaksi_batik.csv'
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR('File CSV tidak ditemukan!'))
            return

        print("\n=== MEMBUAT REKOMENDASI DUA ARAH (BOLAK-BALIK) ===")

        # 1. BACA CSV
        try:
            df = pd.read_csv(file_path)
            if len(df.columns) <= 1: df = pd.read_csv(file_path, sep=';')
            df.columns = df.columns.str.strip()
        except Exception as e:
            print(f"Error CSV: {e}")
            return

        col_items = next((c for c in df.columns if c in ['Items', 'Item', 'Produk']), None)
        if not col_items:
            print("Kolom Items tidak ketemu.")
            return

        # 2. LOAD MAPPING
        valid_map_obj = {}
        for csv_name, db_name in MAPPING_KATEGORI.items():
            kategori = Kategori.objects.filter(nama__iexact=db_name).first()
            if not kategori:
                kategori = Kategori.objects.filter(nama__icontains=db_name).first()

            if kategori:
                count = Produk.objects.filter(kategori=kategori).count()
                if count > 0:
                    valid_map_obj[csv_name] = kategori

        if not valid_map_obj:
            print("GAGAL: Tidak ada kategori valid.")
            return

        # 3. PROSES TRANSAKSI
        transactions = []
        for raw in df[col_items].dropna():
            if not isinstance(raw, str): continue
            parts = raw.split('|') if '|' in raw else raw.split(',')

            clean_cats = []
            for p in parts:
                p = p.strip()
                if p in valid_map_obj:
                    clean_cats.append(valid_map_obj[p])

            unique_cats = sorted(list(set(clean_cats)), key=lambda x: x.id)
            if len(unique_cats) >= 2:
                transactions.append(unique_cats)

        # 4. HITUNG DAN SIMPAN RULES
        pair_counts = Counter()
        for cats in transactions:
            for pair in combinations(cats, 2):
                pair_counts[pair] += 1

        RecommendationRule.objects.all().delete()
        rules_created = 0
        total = len(transactions) if transactions else 1

        print("Sedang menyimpan rules...")

        for pair, freq in pair_counts.items():
            cat_A, cat_B = pair
            support = freq / total
            lift = 1.5

            # --- FUNGSI PEMBUAT RULES (Helper) ---
            def create_link(kategori_sumber, kategori_tujuan):
                count = 0
                # Ambil SEMUA produk sumber
                prods_sumber = Produk.objects.filter(kategori=kategori_sumber)
                # Ambil 5 produk tujuan (rekomendasi)
                prods_tujuan = Produk.objects.filter(kategori=kategori_tujuan)[:5]

                for p_sumber in prods_sumber:
                    for p_tujuan in prods_tujuan:
                        if p_sumber.id == p_tujuan.id: continue

                        if not RecommendationRule.objects.filter(antecedent=p_sumber, consequent=p_tujuan).exists():
                            RecommendationRule.objects.create(
                                antecedent=p_sumber,
                                consequent=p_tujuan,
                                support=support, confidence=0.9, lift=lift
                            )
                            count += 1
                return count

            # === BAGIAN PENTING: JALANKAN DUA ARAH ===

            # ARAH 1: Jika lihat A -> Saran B (Misal: Lihat Batik Cap -> Saran Mentahan)
            rules_created += create_link(cat_A, cat_B)

            # ARAH 2: Jika lihat B -> Saran A (Misal: Lihat Mentahan -> Saran Batik Cap)
            rules_created += create_link(cat_B, cat_A)

        print(f"\nSUKSES! {rules_created} aturan rekomendasi berhasil dibuat (Dua Arah).")