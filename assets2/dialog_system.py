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

Portrait yang ditampilkan otomatis mengikuti karakter aktif player,
diambil lewat character_registry.get_current_character() — TIDAK perlu
di-set manual di sini. Kalau player ganti karakter, portrait ikut berubah
otomatis di percakapan berikutnya.
"""

import pygame
from character_registry import get_current_character

# ================= COLORS (selaras dengan main.py) =================
WHITE  = (255, 255, 255)
BLACK  = (0, 0, 0)
GOLD   = (255, 210, 60)
GREEN  = (80, 220, 140)


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

    # ---------------- CONTROL ----------------
    def open(self, dialog_tree, start_key="start"):
        """Mulai dialog baru dari sebuah dialog tree."""
        self.dialog_tree       = dialog_tree
        self.current_node_key  = start_key
        self.selected_index    = 0
        self.active             = True

    def close(self):
        self.active            = False
        self.dialog_tree        = {}
        self.current_node_key   = None
        self.selected_index     = 0

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

        chosen = options[self.selected_index]
        next_key = chosen.get("next")

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

        # ---- Hint kecil di bawah ----
        hint_font = pygame.font.Font(None, 18)
        hint_surf = hint_font.render("↑/↓ pilih   •   E/Enter konfirmasi   •   ESC tutup", True, (150, 150, 150))
        screen.blit(hint_surf, (box_x + 16, box_y + box_h - 22))

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


# ================= CONTOH DIALOG TREE: PORTAL RESI =================
# Ini contoh isi dialog dengan opsi "abc" / "blabla" sesuai permintaan.
# Gampang dikembangkan: tambah key baru di dict ini, lalu rujuk lewat "next".
RESI_DIALOG_TREE = {
    "start": {
        "speaker": "Resi",
        "text": "Wahai pendekar... apa yang kau cari di tempat suci ini?",
        "options": [
            {"label": "abc",    "next": "node_abc"},
            {"label": "blabla", "next": "node_blabla"},
            {"label": "Pergi",  "next": None},
        ],
    },
    "node_abc": {
        "speaker": "Resi",
        "text": "Kau memilih abc. Jalan ini akan membawamu pada babak berikutnya.",
        "options": [
            {"label": "Kembali", "next": "start"},
            {"label": "Tutup",   "next": None},
        ],
    },
    "node_blabla": {
        "speaker": "Resi",
        "text": "Blabla... begitu katamu. Menarik sekali, pendekar.",
        "options": [
            {"label": "Kembali", "next": "start"},
            {"label": "Tutup",   "next": None},
        ],
    },
}
