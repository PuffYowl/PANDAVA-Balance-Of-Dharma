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

    # ── UPGRADE KEKUATAN — pilih prasasti ────────────────────────
    "node_upgrade": {
        "speaker": "Resi Abimayasa",
        "text": "Prasasti para Pandava tersimpan di sini. Pilih kekuatan mana yang ingin kau serap, pendekar.",
        "options": [
            {"label": "Prasasti Bima",       "next": "node_bima"},
            {"label": "Prasasti Nakula",     "next": "node_nakula"},
            {"label": "Prasasti Arjuna",     "next": "node_arjuna"},
            {"label": "Prasasti Yudhistira", "next": "node_yudhistira"},
        ],
    },
    "node_upgrade_2": {
        "speaker": "Resi Abimayasa",
        "text": "Masih ada satu prasasti lagi yang menunggumu.",
        "options": [
            {"label": "Prasasti Sadewa", "next": "node_sadewa"},
            {"label": "Kembali",          "next": "start"},
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
    # Sadewa: kekuatan menengah, tanpa speed
    "upgrade_strength_sadewa": {
        "damage": +1,
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