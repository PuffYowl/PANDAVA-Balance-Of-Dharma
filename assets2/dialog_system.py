"""
dialog_system.py

Sistem dialog box dengan cabang percakapan (dialog tree), dipakai untuk
NPC seperti "Portal Resi".

Struktur dialog adalah dict bertingkat (node), contoh:

    DIALOG_TREE = {
        "start": {
            "speaker": "Resi",
            "text": "Wahai pendekar, apa yang kau cari?",
            "options": [
                {"label": "abc",    "next": "node_abc"},
                {"label": "blabla", "next": "node_blabla"},
            ],
        },
        "node_abc": {
            "speaker": "Resi",
            "text": "Jawaban untuk pilihan abc...",
            "options": [
                {"label": "Kembali", "next": "start"},
                {"label": "Tutup",   "next": None},   # None = tutup dialog
            ],
        },
        ...
    }

Setiap node punya:
    - "speaker": nama yang bicara (ditampilkan di header box)
    - "text": isi dialog
    - "options": list pilihan, masing-masing punya "label" dan "next"
                 (key node selanjutnya, atau None untuk menutup dialog)

Portrait di DALAM kotak dialog (kiri) otomatis mengikuti karakter aktif
player, diambil lewat character_registry.get_current_character() — TIDAK
perlu di-set manual di sini. Kalau player ganti karakter, portrait ikut
berubah otomatis di percakapan berikutnya.

Portrait NPC (lawan bicara, mis. Resi Abimayasa) ditampilkan secara
TERPISAH, melayang DI ATAS kotak dialog — bukan di dalam box seperti
portrait player. Ini opsional: isi parameter `npc_portrait` saat memanggil
open() dengan path gambar NPC tersebut. Kalau tidak diisi (None), tidak ada
portrait NPC yang ditampilkan (dialog tanpa NPC portrait, seperti sebelumnya).
"""

import pygame
from character_registry import get_current_character

# ================= COLORS (selaras dengan main.py) =================
WHITE  = (255, 255, 255)
BLACK  = (0, 0, 0)
GOLD   = (255, 210, 60)
GREEN  = (80, 220, 140)

# ---- Background abu-abu polos yang menutupi seluruh layar saat dialog
# aktif (lihat penggunaannya di main.py: gameplay tidak digambar sama
# sekali selama dialog berjalan, cukup screen.fill(DIALOG_BG_GRAY)). ----
DIALOG_BG_GRAY = (60, 60, 60)

# Cache gambar NPC portrait yang sudah di-load, supaya tidak re-load dari
# disk setiap frame. Key = (path, target_height).
_NPC_PORTRAIT_CACHE = {}


def _load_npc_portrait(path, target_height):
    """Load gambar portrait NPC dari disk, di-scale berdasarkan TINGGI
    (target_height), dengan lebar dihitung otomatis agar aspect ratio asli
    gambar tetap terjaga (tidak gepeng/stretch) — portrait Resi Abimayasa
    misalnya berbentuk potret (lebih tinggi daripada lebar).

    Hasil di-cache berdasar (path, target_height) supaya tidak re-load dari
    disk setiap frame. Mengembalikan None kalau path None / file tidak
    ditemukan / gagal load — dan saat itu terjadi, mencetak alasannya ke
    konsol (sekali per path) supaya gampang di-debug kalau gambar tidak
    muncul, daripada gagal diam-diam."""
    if not path:
        return None
    cache_key = (path, target_height)
    if cache_key in _NPC_PORTRAIT_CACHE:
        return _NPC_PORTRAIT_CACHE[cache_key]
    try:
        import os
        abs_path = os.path.abspath(path)
        if not os.path.isfile(path):
            print(f"[NPC PORTRAIT] File tidak ditemukan: '{path}' "
                  f"(dicari di: '{abs_path}'). Cek working directory game "
                  f"saat dijalankan — path ini relatif terhadap folder "
                  f"tempat main.py dieksekusi, bukan lokasi file main.py itu sendiri.")
            _NPC_PORTRAIT_CACHE[cache_key] = None
            return None
        img = pygame.image.load(path).convert_alpha()
        src_w, src_h = img.get_size()
        scale_factor = target_height / src_h
        new_w = max(1, round(src_w * scale_factor))
        img = pygame.transform.scale(img, (new_w, target_height))
    except (pygame.error, FileNotFoundError) as e:
        print(f"[NPC PORTRAIT] Gagal load '{path}': {e}")
        _NPC_PORTRAIT_CACHE[cache_key] = None
        return None
    _NPC_PORTRAIT_CACHE[cache_key] = img
    return img


class DialogBox:
    def __init__(self, screen_width, screen_height, font_path="assets2/font/A Friend In Deed.otf"):
        self.screen_w = screen_width
        self.screen_h = screen_height

        self.font_text = pygame.font.Font(font_path, 22)
        self.font_name = pygame.font.Font(font_path, 24)
        self.font_opt  = pygame.font.Font(font_path, 20)

        self.active        = False
        self.dialog_tree    = {}
        self.current_node_key = None
        self.selected_index = 0

        # NPC portrait yang melayang di atas kotak dialog (terpisah dari
        # portrait player di dalam box). None = tidak ada portrait NPC.
        self.npc_portrait_path   = None
        self.npc_portrait_height = 260  # lebar dihitung otomatis (aspect ratio asli dijaga)

        # Set relic yang dimiliki player — di-update dari main.py setiap kali
        # player mengambil relic baru. Berupa set of str, misal {"Batu Arjuna"}.
        # Dipakai untuk validasi sebelum upgrade prasasti diterima Resi.
        self.player_relics: set = set()

        # Flag HP penuh — di-update dari main.py setiap frame atau sebelum
        # dialog dibuka. True = player tidak butuh healing.
        self.player_health_full: bool = False

    # ---------------- CONTROL ----------------
    def open(self, dialog_tree, start_key="start", npc_portrait=None):
        """Mulai dialog baru dari sebuah dialog tree.

        npc_portrait: path opsional ke gambar portrait NPC yang sedang
        bicara (mis. "assets2/npc/resi_abimayasa.png"). Kalau diisi,
        gambar ini ditampilkan melayang DI ATAS kotak dialog selama
        dialog ini aktif. Kalau None, tidak ada portrait NPC ditampilkan.
        """
        self.dialog_tree       = dialog_tree
        self.current_node_key  = start_key
        self.selected_index    = 0
        self.active             = True
        self.npc_portrait_path  = npc_portrait

    def close(self):
        self.active            = False
        self.dialog_tree        = {}
        self.current_node_key   = None
        self.selected_index     = 0
        self.npc_portrait_path  = None

    def _current_node(self):
        if self.current_node_key is None:
            return None
        return self.dialog_tree.get(self.current_node_key)

    # ---------------- INPUT ----------------
    def handle_event(self, event):
        """
        Panggil di event loop SELAMA dialog aktif.
        Return True kalau event ini "dipakai" oleh dialog (supaya main.py
        tidak ikut memproses event yang sama, mis. gerakan player).
        """
        if not self.active:
            return False

        node = self._current_node()
        if node is None:
            self.close()
            return True

        options = node.get("options", [])

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_DOWN, pygame.K_s):
                if options:
                    self.selected_index = (self.selected_index + 1) % len(options)
                return True

            if event.key in (pygame.K_UP, pygame.K_w):
                if options:
                    self.selected_index = (self.selected_index - 1) % len(options)
                return True

            if event.key in (pygame.K_RETURN, pygame.K_e, pygame.K_SPACE):
                self._choose_current_option()
                return True

            if event.key == pygame.K_ESCAPE:
                self.close()
                return True

        return True  # dialog aktif menyerap semua input lain juga

    def _choose_current_option(self):
        node = self._current_node()
        if node is None:
            self.close()
            return

        options = node.get("options", [])
        if not options:
            # Node tanpa opsi = dialog otomatis tutup saat ditekan lanjut
            self.close()
            return

        chosen   = options[self.selected_index]
        next_key = chosen.get("next")

        # ── Cek HP penuh sebelum masuk node healing ──────────────────────
        # Kalau player memilih healing tapi HP sudah penuh, alihkan ke
        # node khusus yang memberi tahu player bahwa HP-nya masih prima.
        if next_key == "node_healing" and self.player_health_full:
            self.current_node_key = "node_healing_full"
            self.selected_index   = 0
            return
        # ─────────────────────────────────────────────────────────────────

        # ── Validasi kepemilikan relic sebelum upgrade ──────────────────
        # Cek apakah node tujuan punya "action" upgrade prasasti.
        # Kalau punya, tapi player belum punya relic yang diperlukan,
        # alihkan ke node penolakan daripada node upgrade.
        if next_key and next_key in self.dialog_tree:
            target_node   = self.dialog_tree[next_key]
            target_action = target_node.get("action", "")
            required_relic = PRASASTI_RELIC_REQUIRED.get(target_action)
            if required_relic and required_relic not in self.player_relics:
                # Player tidak punya prasasti ini — Resi menolak
                self.current_node_key = "node_upgrade_no_relic"
                self.selected_index   = 0
                return
        # ────────────────────────────────────────────────────────────────

        # ── Hapus relic dari inventory setelah upgrade dikonfirmasi ──────
        # Hapus relic tepat saat player menekan "Terima prasasti ini"
        # (yaitu saat berada di node yang ber-action upgrade).
        current_node = self._current_node()
        if current_node:
            current_action = current_node.get("action", "")
            if current_action in PRASASTI_RELIC_REQUIRED:
                relic_to_remove = PRASASTI_RELIC_REQUIRED[current_action]
                self.player_relics.discard(relic_to_remove)
                print(f"[DIALOG] Relic '{relic_to_remove}' dipakai — dihapus dari inventory. "
                      f"Sisa: {self.player_relics}")
        # ─────────────────────────────────────────────────────────────────

        if next_key is None:
            self.close()
        else:
            self.current_node_key = next_key
            self.selected_index   = 0

    # ---------------- DRAW ----------------
    def draw(self, screen):
        if not self.active:
            return

        node = self._current_node()
        if node is None:
            return

        speaker = node.get("speaker", "???")
        text    = node.get("text", "")
        options = node.get("options", [])

        # ---- Layout ----
        box_w = self.screen_w - 80
        box_h = 170
        box_x = 40
        box_y = self.screen_h - box_h - 30

        # ---- NPC portrait (melayang DI ATAS kotak dialog, terpisah dari
        # portrait player di dalam box). Digambar SEBELUM panel box supaya
        # tepi bawahnya sedikit tertutup box — kesannya "berdiri di depan"
        # box, bukan sekadar nempel di atasnya. ----
        npc_portrait = _load_npc_portrait(self.npc_portrait_path, self.npc_portrait_height)
        if npc_portrait is not None:
            npc_w, npc_h = npc_portrait.get_size()
            npc_x = box_x + 24
            npc_y = box_y - npc_h + 28  # naik ke atas box, overlap dikit ke box
            screen.blit(npc_portrait, (npc_x, npc_y))

        # ---- Background panel ----
        panel = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        panel.fill((10, 10, 15, 220))
        screen.blit(panel, (box_x, box_y))
        pygame.draw.rect(screen, GOLD, (box_x, box_y, box_w, box_h), 2, border_radius=8)

        # ---- Portrait (otomatis ikut karakter aktif player) ----
        char_info = get_current_character()
        portrait  = char_info["portrait"]
        portrait_x = box_x + 16
        portrait_y = box_y + 16
        screen.blit(portrait, (portrait_x, portrait_y))
        pygame.draw.rect(screen, WHITE, (portrait_x, portrait_y, portrait.get_width(), portrait.get_height()), 2, border_radius=8)

        text_area_x = portrait_x + portrait.get_width() + 20
        text_area_w = box_w - (portrait.get_width() + 16 + 20) - 220  # sisakan ruang utk opsi di kanan

        # ---- Speaker name ----
        name_surf = self.font_name.render(speaker, True, GOLD)
        screen.blit(name_surf, (text_area_x, box_y + 14))

        # ---- Dialog text (wrap manual sederhana) ----
        wrapped_lines = self._wrap_text(text, self.font_text, text_area_w)
        for i, line in enumerate(wrapped_lines[:3]):  # max 3 baris biar tidak overflow
            line_surf = self.font_text.render(line, True, WHITE)
            screen.blit(line_surf, (text_area_x, box_y + 48 + i * 26))

        # ---- Options (kanan) ----
        opt_x = box_x + box_w - 210
        opt_y = box_y + 16
        for i, opt in enumerate(options):
            is_selected = (i == self.selected_index)
            color = GREEN if is_selected else WHITE
            prefix = "➤ " if is_selected else "   "
            opt_surf = self.font_opt.render(prefix + opt["label"], True, color)
            screen.blit(opt_surf, (opt_x, opt_y + i * 30))


    @staticmethod
    def _wrap_text(text, font, max_width):
        """Word-wrap sederhana berbasis lebar render font."""
        words = text.split(" ")
        lines = []
        current = ""
        for word in words:
            test = (current + " " + word).strip()
            if font.size(test)[0] <= max_width:
                current = test
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines


# ================= DIALOG TREE: PORTAL RESI =================
# "Healing" memulihkan HP player via callback apply_dialog_action().
# "Upgrade Kekuatan" menampilkan sub-menu prasasti Pandava Lima,
# masing-masing memberi buff berbeda (diproses via apply_dialog_action()).
RESI_DIALOG_TREE = {
    "start": {
        "speaker": "Resi Abimayasa",
        "text": "Wahai pendekar Pandava... cahayamu masih menyala. Apa yang kau butuhkan dari Sang Resi?",
        "options": [
            {"label": "Healing",           "next": "node_healing"},
            {"label": "Upgrade Kekuatan",  "next": "node_upgrade"},
            {"label": "Pergi",             "next": None},
        ],
    },

    # ── HEALING ──────────────────────────────────────────────────
    "node_healing": {
        "speaker": "Resi Abimayasa",
        "text": "Tirta suci mengalir untukmu, pendekar. Luka-lukamu akan pulih kembali.",
        "options": [
            {"label": "Terima kasih, Resi", "next": "node_healing_confirm"},
            {"label": "Kembali",             "next": "start"},
        ],
        "action": "healing",
    },
    "node_healing_confirm": {
        "speaker": "Resi Abimayasa",
        "text": "Pergilah dengan sehat, pendekar. Dharma selalu bersamamu.",
        "options": [
            {"label": "Tutup", "next": None},
        ],
    },
    "node_healing_full": {
        "speaker": "Resi Abimayasa",
        "text": "Tubuhmu masih prima, pendekar. Tirta suci ini tidak dibutuhkan — simpan tenagamu untuk pertempuran!",
        "options": [
            {"label": "Baik, Resi", "next": "start"},
        ],
    },

    # ── UPGRADE KEKUATAN — pilih prasasti ────────────────────────
    "node_upgrade": {
        "speaker": "Resi Abimayasa",
        "text": "Prasasti para Pandava tersimpan di sini. Pilih kekuatan mana yang ingin kau serap, pendekar.",
        "options": [
            {"label": "Prasasti Bima",       "next": "node_bima"},
            {"label": "Prasasti Sadewa",     "next": "node_sadewa"},
            {"label": "Prasasti Arjuna",     "next": "node_arjuna"},
            {"label": "Prasasti Nakula",     "next": "node_nakula"},
            {"label": "Prasasti Yudhistira", "next": "node_yudhistira"},
            {"label": "Kembali",             "next": "start"},
        ],
    },

    # ── PRASASTI BIMA — kekuatan tertinggi ───────────────────────
    "node_bima": {
        "speaker": "Resi Abimayasa",
        "text": "Prasasti Bima: kekuatan Sang Werkudara mengalir ke tanganmu. Seranganmu kini jauh lebih mematikan!",
        "options": [
            {"label": "Terima prasasti ini", "next": "node_bima_confirm"},
            {"label": "Kembali",              "next": "node_upgrade"},
        ],
        "action": "upgrade_strength_bima",
    },
    "node_bima_confirm": {
        "speaker": "Resi Abimayasa",
        "text": "Kekuatan Bima kini bersemayam dalam dirimu. Gunakan dengan bijak, pendekar.",
        "options": [
            {"label": "Tutup", "next": None},
        ],
    },

    # ── PRASASTI NAKULA — kecepatan tertinggi ────────────────────
    "node_nakula": {
        "speaker": "Resi Abimayasa",
        "text": "Prasasti Nakula: kelincahan sang kembar suci. Kakimu akan melaju secepat angin!",
        "options": [
            {"label": "Terima prasasti ini", "next": "node_nakula_confirm"},
            {"label": "Kembali",              "next": "node_upgrade"},
        ],
        "action": "upgrade_speed_nakula",
    },
    "node_nakula_confirm": {
        "speaker": "Resi Abimayasa",
        "text": "Kecepatan Nakula kini mengalir di nadimu. Tak ada musuh yang bisa mengejarmu!",
        "options": [
            {"label": "Tutup", "next": None},
        ],
    },

    # ── PRASASTI ARJUNA — kecepatan + kekuatan seimbang ─────────
    "node_arjuna": {
        "speaker": "Resi Abimayasa",
        "text": "Prasasti Arjuna: keseimbangan busur sang ksatria. Kecepatan dan kekuatanmu bertambah bersama.",
        "options": [
            {"label": "Terima prasasti ini", "next": "node_arjuna_confirm"},
            {"label": "Kembali",              "next": "node_upgrade"},
        ],
        "action": "upgrade_arjuna",
    },
    "node_arjuna_confirm": {
        "speaker": "Resi Abimayasa",
        "text": "Harmoni Arjuna kini menjagamu dalam pertempuran. Bidiklah dengan tepat, pendekar!",
        "options": [
            {"label": "Tutup", "next": None},
        ],
    },

    # ── PRASASTI YUDHISTIRA — kecepatan ringan ───────────────────
    "node_yudhistira": {
        "speaker": "Resi Abimayasa",
        "text": "Prasasti Yudhistira: kebijaksanaan sang raja memberimu langkah yang lebih gesit.",
        "options": [
            {"label": "Terima prasasti ini", "next": "node_yudhistira_confirm"},
            {"label": "Kembali",              "next": "node_upgrade"},
        ],
        "action": "upgrade_speed_yudhistira",
    },
    "node_yudhistira_confirm": {
        "speaker": "Resi Abimayasa",
        "text": "Ketenangan Yudhistira memberimu kecepatan dalam setiap langkah. Maju dengan penuh dharma!",
        "options": [
            {"label": "Tutup", "next": None},
        ],
    },

    # ── PENOLAKAN — prasasti belum dimiliki ──────────────────────
    "node_upgrade_no_relic": {
        "speaker": "Resi Abimayasa",
        "text": "Pendekar... kamu belum mempunyai prasasti tersebut. Carilah terlebih dahulu sebelum kau meminta kekuatannya.",
        "options": [
            {"label": "Baik, Resi",  "next": "node_upgrade"},
            {"label": "Kembali",     "next": "start"},
        ],
    },

    # ── PRASASTI SADEWA — kekuatan menengah ──────────────────────
    "node_sadewa": {
        "speaker": "Resi Abimayasa",
        "text": "Prasasti Sadewa: ilmu sang kembar memberkati pukulanmu dengan kekuatan yang lebih dalam.",
        "options": [
            {"label": "Terima prasasti ini", "next": "node_sadewa_confirm"},
            {"label": "Kembali",              "next": "node_upgrade"},
        ],
        "action": "upgrade_strength_sadewa",
    },
    "node_sadewa_confirm": {
        "speaker": "Resi Abimayasa",
        "text": "Kekuatan Sadewa kini ada bersamamu. Setiap pukulanmu membawa makna, pendekar.",
        "options": [
            {"label": "Tutup", "next": None},
        ],
    },
}

# ================= UPGRADE STAT CONFIGS =================
# Besaran buff tiap prasasti — mudah dituning dari sini tanpa
# harus menyentuh kode apply_dialog_action() di main.py.
PRASASTI_BUFFS = {
    # Healing
    "healing": {
        "heal_full": True,                 # pulihkan HP penuh
    },
    # Bima: kekuatan terbesar, tanpa speed
    "upgrade_strength_bima": {
        "damage": +3,
        "speed":  0,
    },
    # Nakula: speed terbesar, tanpa damage
    "upgrade_speed_nakula": {
        "damage": 0,
        "speed":  +2.0,
    },
    # Arjuna: seimbang, tapi lebih kecil dari Bima/Nakula
    "upgrade_arjuna": {
        "damage": +1,
        "speed":  +0.8,
    },
    # Yudhistira: speed kecil, tanpa damage
    "upgrade_speed_yudhistira": {
        "damage": 0,
        "speed":  +0.6,
    },
    # Sadewa: kekuatan menengah — lebih kuat dari Arjuna (+1), lebih lemah dari Bima (+3)
    "upgrade_strength_sadewa": {
        "damage": +2,
        "speed":  0,
    },
}

# ================= PRASASTI → NAMA RELIC =================
# Mapping dari action key upgrade ke nama relic yang harus dimiliki player
# sebelum bisa menukar prasasti tersebut ke Resi.
# Nama harus sama persis dengan RELIC_OPTIONS[...]["name"] di main.py.
PRASASTI_RELIC_REQUIRED = {
    "upgrade_strength_bima":    "Batu Bima",
    "upgrade_speed_nakula":     "Batu Nakula",
    "upgrade_arjuna":           "Batu Arjuna",
    "upgrade_speed_yudhistira": "Batu Yudhistira",
    "upgrade_strength_sadewa":  "Batu Sadewa",
}


# ================= HEALING AURA EFFECT =================
# Efek aura hijau yang muncul di atas karakter player saat mendapat healing.
#
# CARA PAKAI di main.py:
#   1. Buat instance (sekali saja, saat init):
#        from dialog_system import HealingAura
#        healing_aura = HealingAura()
#
#   2. Trigger saat healing diterapkan (di apply_dialog_action):
#        healing_aura.trigger(player.rect.centerx, player.rect.top)
#
#   3. Update + draw setiap frame di game loop (setelah gambar player):
#        healing_aura.update()
#        healing_aura.draw(screen)
#
#   4. Kalau player pindah posisi, update origin setiap frame juga:
#        healing_aura.update_origin(player.rect.centerx, player.rect.top)

import math
import random

class HealingAura:
    """Efek aura hijau berputar yang muncul di atas karakter saat healing.

    Aura terdiri dari dua komponen:
    - Partikel cahaya hijau yang melayang ke atas dan memudar (fade-out)
    - Cincin aura memudar yang mengembang di sekitar karakter

    Durasi total efek: sekitar 90 frame (~1.5 detik di 60fps).
    """

    # Warna-warna aura hijau dengan variasi terang-gelap
    _COLORS = [
        (80,  220, 120),   # hijau sedang
        (50,  255, 100),   # hijau terang
        (120, 255, 160),   # hijau muda
        (30,  200,  80),   # hijau tua
        (180, 255, 200),   # hijau pucat / putih kehijau-hijauan
    ]

    def __init__(self):
        self._particles  = []   # list dict per partikel
        self._rings      = []   # list dict per cincin
        self._origin_x   = 0
        self._origin_y   = 0
        self._active     = False

    # ── Public API ──────────────────────────────────────────────────────

    def trigger(self, cx: int, cy: int):
        """Mulai efek aura di posisi (cx, cy) — biasanya centerx, top karakter."""
        self._origin_x = cx
        self._origin_y = cy
        self._active   = True
        self._particles.clear()
        self._rings.clear()
        self._spawn_burst()

    def update_origin(self, cx: int, cy: int):
        """Perbarui asal efek agar mengikuti karakter yang bergerak."""
        self._origin_x = cx
        self._origin_y = cy

    def update(self):
        """Panggil sekali per frame di game loop untuk memperbarui state."""
        if not self._active:
            return

        # ── Update partikel ──
        alive_p = []
        for p in self._particles:
            p["x"]     += p["vx"]
            p["y"]     += p["vy"]
            p["vy"]    -= 0.05             # gravitasi terbalik (melayang ke atas)
            p["alpha"] -= p["fade"]
            p["size"]  = max(1, p["size"] - 0.06)
            if p["alpha"] > 0:
                alive_p.append(p)
        self._particles = alive_p

        # Spawn partikel baru selama ada ring (efek masih berjalan)
        if self._rings:
            self._spawn_particles(count=2)

        # ── Update cincin ──
        alive_r = []
        for r in self._rings:
            r["radius"] += r["expand"]
            r["alpha"]  -= r["fade"]
            if r["alpha"] > 0:
                alive_r.append(r)
        self._rings = alive_r

        # Nonaktifkan kalau semua sudah hilang
        if not self._particles and not self._rings:
            self._active = False

    def draw(self, screen: pygame.Surface):
        """Gambar aura ke screen. Panggil setelah gambar player agar di atas."""
        if not self._active:
            return

        # ── Gambar cincin ──
        for r in self._rings:
            alpha = max(0, min(255, int(r["alpha"])))
            if alpha == 0:
                continue
            color = r["color"]
            radius = int(r["radius"])
            if radius < 2:
                continue
            # Buat surface transparan, gambar lingkaran, lalu blit ke screen
            diam = radius * 2 + 4
            ring_surf = pygame.Surface((diam, diam), pygame.SRCALPHA)
            pygame.draw.circle(
                ring_surf,
                (*color, alpha),
                (diam // 2, diam // 2),
                radius,
                width=2,
            )
            screen.blit(ring_surf, (self._origin_x - diam // 2,
                                    self._origin_y - diam // 2))

        # ── Gambar partikel ──
        for p in self._particles:
            alpha = max(0, min(255, int(p["alpha"])))
            if alpha == 0:
                continue
            size = max(1, int(p["size"]))
            diam = size * 2
            p_surf = pygame.Surface((diam, diam), pygame.SRCALPHA)
            pygame.draw.circle(
                p_surf,
                (*p["color"], alpha),
                (size, size),
                size,
            )
            screen.blit(p_surf, (int(p["x"]) - size, int(p["y"]) - size))

    @property
    def is_active(self) -> bool:
        """True selama efek masih berjalan."""
        return self._active

    # ── Internal helpers ────────────────────────────────────────────────

    def _spawn_burst(self):
        """Spawn partikel awal + 3 cincin sekaligus saat trigger dipanggil."""
        self._spawn_particles(count=30)
        for i in range(3):
            delay_radius = 8 + i * 6
            self._rings.append({
                "radius": delay_radius,
                "expand": 1.8 + i * 0.4,
                "alpha":  220 - i * 40,
                "fade":   3.5 + i * 0.5,
                "color":  random.choice(self._COLORS),
            })

    def _spawn_particles(self, count: int = 5):
        """Spawn sejumlah partikel acak dari titik origin."""
        for _ in range(count):
            angle  = random.uniform(0, math.tau)
            speed  = random.uniform(0.4, 2.2)
            spread = random.uniform(0, 28)     # jarak lateral dari center
            self._particles.append({
                "x":     self._origin_x + math.cos(angle) * spread,
                "y":     self._origin_y + random.uniform(-5, 8),
                "vx":    math.cos(angle) * speed * 0.4,
                "vy":    -random.uniform(0.8, 2.5),   # arah ke atas
                "size":  random.uniform(2.5, 5.5),
                "alpha": random.uniform(180, 255),
                "fade":  random.uniform(3, 7),
                "color": random.choice(self._COLORS),
            })


# ================= UPGRADE AURA EFFECT =================
# Efek aura seperti api yang muncul di sekitar karakter saat menerima upgrade prasasti.
# Mendukung dua tema warna: emas (Bima) dan hijau (Arjuna).
#
# CARA PAKAI di main.py:
#   1. Import & buat instance (sekali saja):
#        from dialog_system import UpgradeAura
#        upgrade_aura = UpgradeAura()
#
#   2. Trigger dengan warna yang sesuai (di apply_dialog_action):
#        upgrade_aura.trigger(player.rect.centerx, player.rect.centery, theme="gold")   # Bima
#        upgrade_aura.trigger(player.rect.centerx, player.rect.centery, theme="green")  # Arjuna
#
#   3. Update + draw setiap frame SETELAH player digambar:
#        upgrade_aura.update_origin(player.rect.centerx, player.rect.centery)
#        upgrade_aura.update()
#        upgrade_aura.draw(screen)

class UpgradeAura:
    """Efek aura api yang mengelilingi karakter saat menerima upgrade prasasti.

    Berbeda dari HealingAura yang partikelnya naik ke atas (seperti cahaya),
    UpgradeAura mensimulasikan kobaran api — partikel bergerak naik dengan
    turbulensi lateral (goyang kiri-kanan), ukuran besar di bawah mengecil
    di atas, dan ada lapisan inner glow di tengah karakter.

    Tema:
        "gold"  — api emas/oranye untuk Bima (kekuatan brutal Werkudara)
        "green" — api hijau untuk Arjuna (keseimbangan ksatria)
    Durasi: ~2 detik (120 frame di 60fps).
    """

    _PALETTES = {
        "gold": [
            (255, 200,  40),   # kuning emas terang
            (255, 140,  10),   # oranye api
            (255, 80,    0),   # merah-oranye
            (255, 230, 100),   # emas pucat
            (255, 255, 160),   # putih kekuningan (ujung lidah api)
        ],
        "green": [
            (60,  255, 120),   # hijau neon
            (30,  200,  80),   # hijau tua
            (140, 255, 180),   # hijau muda
            (200, 255, 100),   # hijau-kuning (ujung api)
            (80,  255, 200),   # cyan-hijau
        ],
    }

    def __init__(self):
        self._particles  = []
        self._rings      = []
        self._embers     = []   # percikan kecil yang jatuh ke bawah (ember/bara)
        self._origin_x   = 0
        self._origin_y   = 0
        self._active     = False
        self._theme      = "gold"
        self._frame      = 0   # counter frame sejak trigger, untuk continuous spawn

    # ── Public API ──────────────────────────────────────────────────────

    def trigger(self, cx: int, cy: int, theme: str = "gold"):
        """Mulai efek aura api.

        cx, cy  : pusat karakter (rect.centerx, rect.centery)
        theme   : "gold" untuk Bima, "green" untuk Arjuna
        """
        self._origin_x = cx
        self._origin_y = cy
        self._theme    = theme if theme in self._PALETTES else "gold"
        self._active   = True
        self._frame    = 0
        self._particles.clear()
        self._rings.clear()
        self._embers.clear()
        self._spawn_burst()

    def update_origin(self, cx: int, cy: int):
        self._origin_x = cx
        self._origin_y = cy

    def update(self):
        if not self._active:
            return

        self._frame += 1
        colors = self._PALETTES[self._theme]

        # Continuous spawn selama efek berlangsung (makin lama makin sedikit)
        if self._frame < 80:
            self._spawn_fire_particles(count=4, colors=colors)
        if self._frame < 60 and self._frame % 8 == 0:
            self._spawn_ring(colors)
        if self._frame % 12 == 0 and self._frame < 100:
            self._spawn_ember(colors)

        # ── Update partikel api ──
        alive_p = []
        for p in self._particles:
            p["x"]  += p["vx"] + math.sin(p["phase"] + self._frame * 0.18) * 0.5
            p["y"]  += p["vy"]
            p["vy"] -= 0.08               # naik lebih cepat dari HealingAura
            p["alpha"] -= p["fade"]
            p["size"]  = max(0.5, p["size"] - 0.12)  # mengecil lebih cepat (lidah api)
            p["phase"] += 0.2
            if p["alpha"] > 0:
                alive_p.append(p)
        self._particles = alive_p

        # ── Update cincin ──
        alive_r = []
        for r in self._rings:
            r["radius"] += r["expand"]
            r["alpha"]  -= r["fade"]
            if r["alpha"] > 0:
                alive_r.append(r)
        self._rings = alive_r

        # ── Update ember (percikan jatuh) ──
        alive_e = []
        for e in self._embers:
            e["x"]     += e["vx"]
            e["y"]     += e["vy"]
            e["vy"]    += 0.15            # gravitasi normal (jatuh ke bawah)
            e["alpha"] -= e["fade"]
            if e["alpha"] > 0:
                alive_e.append(e)
        self._embers = alive_e

        if not self._particles and not self._rings and not self._embers:
            self._active = False

    def draw(self, screen: pygame.Surface):
        if not self._active:
            return

        # ── Gambar cincin ──
        for r in self._rings:
            alpha = max(0, min(255, int(r["alpha"])))
            if alpha == 0:
                continue
            radius = int(r["radius"])
            if radius < 2:
                continue
            diam = radius * 2 + 4
            ring_surf = pygame.Surface((diam, diam), pygame.SRCALPHA)
            pygame.draw.circle(
                ring_surf,
                (*r["color"], alpha),
                (diam // 2, diam // 2),
                radius,
                width=3,
            )
            screen.blit(ring_surf, (self._origin_x - diam // 2,
                                    self._origin_y - diam // 2))

        # ── Gambar partikel api ──
        for p in self._particles:
            alpha = max(0, min(255, int(p["alpha"])))
            if alpha == 0:
                continue
            size = max(1, int(p["size"]))
            diam = size * 2
            p_surf = pygame.Surface((diam, diam), pygame.SRCALPHA)
            pygame.draw.circle(p_surf, (*p["color"], alpha), (size, size), size)
            screen.blit(p_surf, (int(p["x"]) - size, int(p["y"]) - size))

        # ── Gambar ember ──
        for e in self._embers:
            alpha = max(0, min(255, int(e["alpha"])))
            if alpha == 0:
                continue
            size = max(1, int(e["size"]))
            diam = size * 2
            e_surf = pygame.Surface((diam, diam), pygame.SRCALPHA)
            pygame.draw.circle(e_surf, (*e["color"], alpha), (size, size), size)
            screen.blit(e_surf, (int(e["x"]) - size, int(e["y"]) - size))

    @property
    def is_active(self) -> bool:
        return self._active

    # ── Internal helpers ────────────────────────────────────────────────

    def _spawn_burst(self):
        """Burst awal: banyak partikel + 2 cincin eksplosif."""
        colors = self._PALETTES[self._theme]
        self._spawn_fire_particles(count=40, colors=colors)
        for i in range(2):
            self._rings.append({
                "radius": 10 + i * 8,
                "expand": 2.5 + i * 0.6,
                "alpha":  240 - i * 50,
                "fade":   4.0 + i * 0.8,
                "color":  random.choice(colors),
            })
        # Ember burst awal
        self._spawn_ember(colors, count=8)

    def _spawn_fire_particles(self, count: int, colors: list):
        """Partikel api yang muncul dari sekeliling karakter."""
        for _ in range(count):
            angle  = random.uniform(0, math.tau)
            spread = random.uniform(10, 36)   # radius dari center karakter
            # Partikel muncul di sepanjang tubuh karakter (bukan cuma di atas)
            offset_y = random.uniform(-20, 20)
            self._particles.append({
                "x":     self._origin_x + math.cos(angle) * spread,
                "y":     self._origin_y + offset_y,
                "vx":    math.cos(angle) * random.uniform(0.2, 1.0),
                "vy":    -random.uniform(1.5, 3.5),   # naik cepat
                "size":  random.uniform(3.0, 7.0),    # lebih besar dari healing
                "alpha": random.uniform(200, 255),
                "fade":  random.uniform(4, 9),
                "color": random.choice(colors),
                "phase": random.uniform(0, math.tau),  # fase turbulensi lateral
            })

    def _spawn_ring(self, colors: list):
        """Cincin aura baru yang mengembang."""
        self._rings.append({
            "radius": random.uniform(8, 18),
            "expand": random.uniform(1.5, 2.8),
            "alpha":  random.uniform(160, 220),
            "fade":   random.uniform(5, 9),
            "color":  random.choice(colors),
        })

    def _spawn_ember(self, colors: list, count: int = 3):
        """Percikan kecil yang terlempar ke atas lalu jatuh (efek bara api)."""
        for _ in range(count):
            angle = random.uniform(0, math.tau)
            self._embers.append({
                "x":     self._origin_x + math.cos(angle) * random.uniform(5, 20),
                "y":     self._origin_y + random.uniform(-15, 5),
                "vx":    math.cos(angle) * random.uniform(1.0, 3.0),
                "vy":    -random.uniform(2.0, 4.5),
                "size":  random.uniform(1.5, 3.0),
                "alpha": random.uniform(200, 255),
                "fade":  random.uniform(3, 6),
                "color": random.choice(colors),
            })