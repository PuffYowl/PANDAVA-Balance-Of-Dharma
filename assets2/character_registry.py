"""
character_registry.py

Sistem "broadcast" identitas karakter.

Ide dasarnya:
- Setiap class karakter (Mage, Assasin, Satyr, Archer, Spear, Hammer, dst)
  didaftarkan SEKALI di CHARACTER_REGISTRY dengan metadata-nya
  (nama tampilan, path/placeholder portrait, warna, dll).
- Saat player dibuat / berganti karakter di character_select(), panggil
  broadcast_character(player) SEKALI. Fungsi ini akan:
    1. Mendeteksi class dari objek player itu.
    2. Mengambil metadata dari registry.
    3. Menyimpannya sebagai "current" character info yang bisa diakses
       di mana saja lewat get_current_character().

Jadi dialog_system.py (atau sistem manapun) TIDAK PERLU tahu detail
class player. Dia cuma panggil get_current_character() dan dapat
portrait + nama yang selalu sinkron dengan karakter yang sedang dipakai.

Kalau nanti ada karakter baru, cukup tambah satu entry di CHARACTER_REGISTRY,
tidak perlu ubah dialog_system.py sama sekali.
"""

import pygame

# ================= PLACEHOLDER PORTRAIT =================
# Placeholder sederhana: kotak warna + inisial nama, dibuat lewat kode
# (bukan file gambar), supaya tidak error kalau asetnya belum ada.
# Nanti kalau sudah ada file asli, tinggal ganti "portrait_path" di
# registry di bawah dan loader akan otomatis pakai file itu.

_PLACEHOLDER_CACHE = {}

def _make_placeholder_portrait(label, color, size=(140, 140)):
    """Generate portrait placeholder di memori (tidak butuh file)."""
    cache_key = (label, color, size)
    if cache_key in _PLACEHOLDER_CACHE:
        return _PLACEHOLDER_CACHE[cache_key]

    surf = pygame.Surface(size, pygame.SRCALPHA)
    pygame.draw.rect(surf, color, surf.get_rect(), border_radius=12)
    pygame.draw.rect(surf, (255, 255, 255), surf.get_rect(), width=3, border_radius=12)

    font = pygame.font.Font(None, 64)
    initial = label[0].upper() if label else "?"
    text_surf = font.render(initial, True, (255, 255, 255))
    surf.blit(text_surf, text_surf.get_rect(center=(size[0] // 2, size[1] // 2)))

    _PLACEHOLDER_CACHE[cache_key] = surf
    return surf


def _load_portrait(entry):
    """
    Coba load portrait dari file jika 'portrait_path' diisi dan file ada.
    Kalau tidak ada / gagal, fallback ke placeholder buatan.
    """
    path = entry.get("portrait_path")
    if path:
        try:
            img = pygame.image.load(path).convert_alpha()
            return pygame.transform.scale(img, entry.get("portrait_size", (140, 140)))
        except (pygame.error, FileNotFoundError):
            pass  # fallback ke placeholder di bawah

    return _make_placeholder_portrait(
        entry["display_name"],
        entry.get("color", (90, 90, 90)),
        entry.get("portrait_size", (140, 140)),
    )


# ================= REGISTRY =================
# Key = nama class Python persis (mis. "Assasin", "Mage", "Satyr", "Archer").
# Tambah karakter baru cukup tambah satu dict di sini.
CHARACTER_REGISTRY = {
    "Mage": {
        "display_name": "Mage",
        "portrait_path": None,   # contoh nanti: "assets2/portraits/mage.png"
        "color": (120, 80, 220),
    },
    "Assasin": {
        "display_name": "Assasin",
        "portrait_path": None,
        "color": (60, 60, 60),
    },
    "Satyr": {
        "display_name": "Satyr",
        "portrait_path": None,
        "color": (150, 110, 60),
    },
    "Archer": {
        "display_name": "Archer",
        "portrait_path": None,
        "color": (60, 140, 70),
    },
    "Spear": {
        "display_name": "Spear",
        "portrait_path": None,
        "color": (200, 170, 40),
    },
    "Hammer": {
        "display_name": "Hammer",
        "portrait_path": None,
        "color": (180, 70, 70),
    },
}

# Fallback kalau class player tidak ditemukan di registry
_UNKNOWN_ENTRY = {
    "display_name": "Unknown",
    "portrait_path": None,
    "color": (100, 100, 100),
}

# ================= STATE "CURRENT CHARACTER" =================
_current_character = None  # dict hasil broadcast terakhir


def broadcast_character(player_obj):
    """
    Panggil fungsi ini SETIAP KALI player dibuat / berganti karakter
    (contoh: di character_select() setelah `player = selected_class(...)`).

    Ini akan mendeteksi class dari player_obj, mengambil metadata dari
    CHARACTER_REGISTRY, melakukan load/generate portrait, lalu menyimpannya
    sebagai "current character" yang bisa diakses lewat get_current_character().
    """
    global _current_character

    class_name = type(player_obj).__name__
    entry = CHARACTER_REGISTRY.get(class_name, _UNKNOWN_ENTRY)

    portrait_surf = _load_portrait(entry)

    _current_character = {
        "class_name": class_name,
        "display_name": entry["display_name"],
        "portrait": portrait_surf,
        "color": entry.get("color", (100, 100, 100)),
    }

    print(f"[BROADCAST] Karakter aktif sekarang: {_current_character['display_name']} ({class_name})")
    return _current_character


def get_current_character():
    """
    Dipanggil dari sistem manapun (dialog box, HUD, dll) untuk mendapatkan
    info karakter yang sedang aktif. Selalu sinkron karena di-update lewat
    broadcast_character() setiap kali karakter berubah.

    Return dict: {"class_name", "display_name", "portrait" (Surface), "color"}
    """
    global _current_character
    if _current_character is None:
        # Belum pernah broadcast — kembalikan fallback aman
        return {
            "class_name": "Unknown",
            "display_name": _UNKNOWN_ENTRY["display_name"],
            "portrait": _load_portrait(_UNKNOWN_ENTRY),
            "color": _UNKNOWN_ENTRY["color"],
        }
    return _current_character
