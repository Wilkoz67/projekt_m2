"""
Projekt M-II: Chaotyczne przekształcanie obrazu cyfrowego
Autor: Student
Cel: Demonstracja mechanizmów permutacji, substytucji i chaosu w przetwarzaniu obrazu.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import numpy as np
from PIL import Image, ImageTk
import os
import math


# ============================================================
# ETAP 1: Naiwny scrambling
# ============================================================

class NaiveScrambler:
    """
    Etap 1: Prosty scrambling przez przesunięcie wierszy i kolumn.
    Klucz: shift (int) - liczba pozycji przesunięcia.
    Słabość: zachowuje strukturę lokalną pikseli, widoczne wzorce.
    """

    def scramble(self, img_array: np.ndarray, key: int) -> np.ndarray:
        arr = img_array.copy()
        h, w = arr.shape[:2]
        for i in range(h):
            shift = (i * key) % w
            arr[i] = np.roll(arr[i], shift, axis=0)
        result = arr.copy()
        for j in range(w):
            shift = (j * key) % h
            result[:, j] = np.roll(arr[:, j], shift, axis=0)
        return result

    def unscramble(self, img_array: np.ndarray, key: int) -> np.ndarray:
        arr = img_array.copy()
        h, w = arr.shape[:2]
        result = arr.copy()
        for j in range(w):
            shift = (j * key) % h
            result[:, j] = np.roll(arr[:, j], -shift, axis=0)
        arr = result.copy()
        for i in range(h):
            shift = (i * key) % w
            arr[i] = np.roll(result[i], -shift, axis=0)
        return arr


# ============================================================
# ETAP 2: Czysta permutacja sterowana kluczem (Fisher-Yates)
# ============================================================

class KeyedPermutationScrambler:
    """
    Etap 2: Czysta permutacja pikseli sterowana kluczem (seed).
    """

    def _generate_permutation(self, n: int, seed: int):
        rng = np.random.default_rng(seed)
        perm = np.arange(n)
        rng.shuffle(perm)
        perm_inv = np.empty_like(perm)
        perm_inv[perm] = np.arange(n)
        return perm, perm_inv

    def scramble(self, img_array: np.ndarray, seed: int) -> np.ndarray:
        h, w = img_array.shape[:2]
        n = h * w
        channels = img_array.shape[2] if img_array.ndim == 3 else 1
        flat = img_array.reshape(n, -1) if channels > 1 else img_array.reshape(n)
        perm, _ = self._generate_permutation(n, seed)
        scrambled_flat = flat[perm]
        return scrambled_flat.reshape(img_array.shape)

    def unscramble(self, img_array: np.ndarray, seed: int) -> np.ndarray:
        h, w = img_array.shape[:2]
        n = h * w
        channels = img_array.shape[2] if img_array.ndim == 3 else 1
        flat = img_array.reshape(n, -1) if channels > 1 else img_array.reshape(n)
        _, perm_inv = self._generate_permutation(n, seed)
        unscrambled_flat = flat[perm_inv]
        return unscrambled_flat.reshape(img_array.shape)

    def verify_inverse(self, n: int, seed: int) -> bool:
        perm, perm_inv = self._generate_permutation(n, seed)
        identity = perm_inv[perm]
        return np.all(identity == np.arange(n))


# ============================================================
# ETAP 3: Mechanizm wzmacniający - Substytucja deterministyczna
# ============================================================

class HybridScrambler:
    """
    Etap 3: Hybryda - Permutacja + Substytucja deterministyczna.
    """

    def __init__(self):
        self.permuter = KeyedPermutationScrambler()

    def _generate_xor_mask(self, shape, seed: int) -> np.ndarray:
        rng = np.random.default_rng(seed + 99999)
        mask = rng.integers(0, 256, size=shape, dtype=np.uint8)
        return mask

    def scramble(self, img_array: np.ndarray, seed: int) -> np.ndarray:
        permuted = self.permuter.scramble(img_array, seed)
        mask = self._generate_xor_mask(permuted.shape, seed)
        result = (permuted.astype(np.int32) ^ mask.astype(np.int32)).astype(np.uint8)
        return result

    def unscramble(self, img_array: np.ndarray, seed: int) -> np.ndarray:
        mask = self._generate_xor_mask(img_array.shape, seed)
        desubstituted = (img_array.astype(np.int32) ^ mask.astype(np.int32)).astype(np.uint8)
        result = self.permuter.unscramble(desubstituted, seed)
        return result


# ============================================================
# METRYKI ANALITYCZNE
# ============================================================

def compute_correlation(img_array: np.ndarray) -> float:
    if img_array.ndim == 3:
        gray = np.mean(img_array, axis=2)
    else:
        gray = img_array.astype(float)
    gray = gray.astype(float)
    h, w = gray.shape
    if w < 2:
        return 0.0
    x = gray[:, :-1].flatten()
    y = gray[:, 1:].flatten()
    if np.std(x) == 0 or np.std(y) == 0:
        return 1.0
    corr = np.corrcoef(x, y)[0, 1]
    return float(corr)


def compute_pixel_difference(img1: np.ndarray, img2: np.ndarray) -> float:
    diff = np.abs(img1.astype(float) - img2.astype(float))
    return float(np.mean(diff))


def compute_psnr(original: np.ndarray, recovered: np.ndarray) -> float:
    mse = np.mean((original.astype(float) - recovered.astype(float)) ** 2)
    if mse == 0:
        return float('inf')
    return 20 * math.log10(255.0 / math.sqrt(mse))


# ============================================================
# PALETA KOLORÓW
# ============================================================

THEME = {
    "bg_dark":    "#080812",
    "bg_mid":     "#0d0d20",
    "bg_panel":   "#111128",
    "bg_input":   "#16163a",
    "accent":     "#00e5b0",
    "accent2":    "#7b5ea7",
    "text_main":  "#d0d8f0",
    "text_dim":   "#5a6080",
    "text_muted": "#3a4060",
    "red":        "#ff5555",
    "orange":     "#ffaa44",
    "blue":       "#44aaff",
    "green":      "#44dd88",
    "yellow":     "#ffdd44",
    "border":     "#1e1e40",
}

# Kolory paneli obrazów (border + title bar)
PANEL_COLORS = ["#00e5b0", "#ff8833", "#4499ff"]
PANEL_BG      = "#0a0a1e"


# ============================================================
# GUI
# ============================================================

class ImageScrambleGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Projekt M-II – Chaotyczne przekształcanie obrazu cyfrowego")
        self.root.configure(bg=THEME["bg_dark"])
        self.root.geometry("1440x920")
        self.root.minsize(1100, 750)

        self.original_array  = None
        self.scrambled_array = None
        self.recovered_array = None

        self.naive    = NaiveScrambler()
        self.permuter = KeyedPermutationScrambler()
        self.hybrid   = HybridScrambler()

        self._build_ui()

    # ----------------------------------------------------------
    # BUDOWA INTERFEJSU
    # ----------------------------------------------------------

    def _build_ui(self):
        self._build_header()

        main = tk.Frame(self.root, bg=THEME["bg_dark"])
        main.pack(fill=tk.BOTH, expand=True, padx=12, pady=(6, 0))

        # Lewa kolumna: panel sterowania
        ctrl = tk.Frame(main, bg=THEME["bg_panel"], width=290)
        ctrl.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10), pady=0)
        ctrl.pack_propagate(False)
        self._build_controls(ctrl)

        # Prawa kolumna
        right = tk.Frame(main, bg=THEME["bg_dark"])
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        img_frame = tk.Frame(right, bg=THEME["bg_dark"])
        img_frame.pack(fill=tk.BOTH, expand=True)
        self._build_image_panels(img_frame)

        metrics_frame = tk.Frame(right, bg=THEME["bg_panel"], height=140)
        metrics_frame.pack(fill=tk.X, pady=(10, 0))
        metrics_frame.pack_propagate(False)
        self._build_metrics(metrics_frame)

        self._build_statusbar()

    def _build_header(self):
        top = tk.Frame(self.root, bg=THEME["bg_mid"], height=68)
        top.pack(fill=tk.X)
        top.pack_propagate(False)

        left = tk.Frame(top, bg=THEME["bg_mid"])
        left.pack(side=tk.LEFT, padx=22, pady=0, fill=tk.Y)

        tk.Label(
            left, text="PROJEKT M-II",
            font=("Courier New", 17, "bold"),
            fg=THEME["accent"], bg=THEME["bg_mid"]
        ).pack(anchor="w", pady=(12, 0))

        tk.Label(
            left, text="Chaotyczne przekształcanie obrazu cyfrowego",
            font=("Courier New", 9),
            fg=THEME["text_dim"], bg=THEME["bg_mid"]
        ).pack(anchor="w")

        # Etykieta z prawej
        tk.Label(
            top,
            text="Permutacja  ·  Substytucja  ·  XOR",
            font=("Courier New", 8),
            fg=THEME["text_muted"], bg=THEME["bg_mid"]
        ).pack(side=tk.RIGHT, padx=22, anchor="center")

        # Linia akcentu na dole headera
        accent_line = tk.Frame(self.root, bg=THEME["accent"], height=2)
        accent_line.pack(fill=tk.X)

    def _build_statusbar(self):
        bar = tk.Frame(self.root, bg=THEME["bg_mid"], height=24)
        bar.pack(fill=tk.X, side=tk.BOTTOM)
        bar.pack_propagate(False)

        self.status_var = tk.StringVar(value="Gotowy  ·  Wczytaj obraz aby rozpocząć")
        tk.Label(
            bar, textvariable=self.status_var,
            font=("Courier New", 8),
            fg=THEME["text_dim"], bg=THEME["bg_mid"]
        ).pack(side=tk.LEFT, padx=14, pady=4)

        tk.Label(
            bar, text="Projekt M-II  ·  2024",
            font=("Courier New", 8),
            fg=THEME["text_muted"], bg=THEME["bg_mid"]
        ).pack(side=tk.RIGHT, padx=14)

    # ----------------------------------------------------------
    # PANEL STEROWANIA
    # ----------------------------------------------------------

    def _build_controls(self, parent):
        # === SEKCJA: Plik ===
        self._section_header(parent, "PLIK")
        self._btn(parent, "  Wczytaj obraz", self._load_image,
                  color="#1a3a2a", hover="#256040", accent=THEME["accent"])

        self._divider(parent)

        # === SEKCJA: Etap ===
        self._section_header(parent, "ALGORYTM")

        self.stage_var = tk.IntVar(value=1)
        stage_defs = [
            (1, "Etap 1", "Naiwny scrambling",    "#1a2a3a", "#00aaff"),
            (2, "Etap 2", "Czysta permutacja",    "#2a1a3a", "#aa66ff"),
            (3, "Etap 3", "Hybrydowy (P + XOR)", "#1a2a1a", "#44cc88"),
        ]

        self.rb_frames = {}
        for val, short, long, bg, col in stage_defs:
            f = tk.Frame(parent, bg=bg, cursor="hand2")
            f.pack(fill=tk.X, padx=12, pady=2)

            rb = tk.Radiobutton(
                f, text=f" {short}  –  {long}",
                variable=self.stage_var, value=val,
                font=("Courier New", 8, "bold"),
                fg=col, bg=bg,
                selectcolor=THEME["bg_dark"],
                activebackground=bg, activeforeground=col,
                indicatoron=True,
                command=self._on_stage_change
            )
            rb.pack(padx=8, pady=5, anchor="w")
            self.rb_frames[val] = (f, bg, col)

            # Efekt hover
            for widget in (f, rb):
                widget.bind("<Enter>", lambda e, fr=f, c=col: fr.config(bg=c, relief=tk.FLAT))
                widget.bind("<Leave>", lambda e, fr=f, bg_=bg: fr.config(bg=bg_))

        self._divider(parent)

        # === SEKCJA: Klucze ===
        self._section_header(parent, "KLUCZE")

        self._field_label(parent, "Klucz poprawny (seed / shift):")
        self.key_var = tk.StringVar(value="42")
        self._entry(parent, self.key_var, fg=THEME["accent"])

        self._field_label(parent, "Klucz błędny (test):")
        self.wrong_key_var = tk.StringVar(value="43")
        self._entry(parent, self.wrong_key_var, fg=THEME["red"])

        self.use_wrong_key = tk.BooleanVar(value=False)
        cb_frame = tk.Frame(parent, bg=THEME["bg_panel"])
        cb_frame.pack(fill=tk.X, padx=12, pady=(0, 6))
        cb = tk.Checkbutton(
            cb_frame, text=" Użyj błędnego klucza przy operacjach",
            variable=self.use_wrong_key,
            font=("Courier New", 8), fg=THEME["orange"], bg=THEME["bg_panel"],
            selectcolor=THEME["bg_dark"],
            activebackground=THEME["bg_panel"], activeforeground=THEME["orange"]
        )
        cb.pack(padx=4, anchor="w", pady=3)

        self._divider(parent)

        # === SEKCJA: Operacje ===
        self._section_header(parent, "OPERACJE")
        self._btn(parent, "  SCRAMBLE",         self._scramble,      color="#1a3020", hover="#265540", accent="#44dd88")
        self._btn(parent, "  UNSCRAMBLE",        self._unscramble,    color="#1a2040", hover="#263060", accent="#4499ff")
        self._btn(parent, "  Analiza + metryki", self._run_analysis,  color="#2a1840", hover="#3d2860", accent="#aa66ff")

        self._divider(parent)

        self._btn(parent, "  Zapisz wyniki",     self._save_results,  color="#1e1e30", hover="#2a2a48", accent="#556688")

        # Info o etapie i weryfikacja
        self.verify_label = tk.Label(
            parent, text="", font=("Courier New", 8),
            fg=THEME["green"], bg=THEME["bg_panel"], wraplength=255
        )
        self.verify_label.pack(padx=10, pady=4)

        self.stage_info = tk.Label(
            parent, text="", font=("Courier New", 8),
            fg=THEME["text_dim"], bg=THEME["bg_panel"], wraplength=255,
            justify=tk.LEFT
        )
        self.stage_info.pack(padx=14, pady=(0, 8), anchor="w")
        self._on_stage_change()

    # --- Helpers UI ---

    def _section_header(self, parent, text):
        f = tk.Frame(parent, bg=THEME["bg_panel"])
        f.pack(fill=tk.X, padx=12, pady=(10, 2))
        tk.Label(
            f, text=text,
            font=("Courier New", 8, "bold"),
            fg=THEME["accent"], bg=THEME["bg_panel"]
        ).pack(side=tk.LEFT)
        tk.Frame(f, bg=THEME["border"], height=1).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 0), pady=6
        )

    def _divider(self, parent):
        tk.Frame(parent, bg=THEME["border"], height=1).pack(
            fill=tk.X, padx=12, pady=6
        )

    def _field_label(self, parent, text):
        tk.Label(
            parent, text=text,
            font=("Courier New", 8),
            fg=THEME["text_dim"], bg=THEME["bg_panel"]
        ).pack(padx=14, anchor="w", pady=(2, 0))

    def _entry(self, parent, var, fg=None):
        e = tk.Entry(
            parent, textvariable=var,
            font=("Courier New", 12, "bold"),
            bg=THEME["bg_input"], fg=fg or THEME["accent"],
            insertbackground=fg or THEME["accent"],
            relief=tk.FLAT, bd=0, highlightthickness=1,
            highlightbackground=THEME["border"],
            highlightcolor=THEME["accent"]
        )
        e.pack(padx=14, pady=(2, 8), fill=tk.X, ipady=4)
        return e

    def _btn(self, parent, text, cmd, color="#1e1e30", hover="#2a2a48", accent="#556688"):
        btn = tk.Button(
            parent, text=text, command=cmd,
            font=("Courier New", 9, "bold"),
            fg=accent, bg=color,
            activebackground=hover, activeforeground=accent,
            relief=tk.FLAT, bd=0,
            padx=10, pady=9, cursor="hand2",
            anchor="w"
        )
        btn.pack(padx=12, pady=3, fill=tk.X)
        btn.bind("<Enter>", lambda e, b=btn, h=hover: b.config(bg=h))
        btn.bind("<Leave>", lambda e, b=btn, c=color: b.config(bg=c))
        return btn

    # ----------------------------------------------------------
    # PANELE OBRAZÓW
    # ----------------------------------------------------------

    def _build_image_panels(self, parent):
        titles      = ["ORYGINAŁ",      "PRZEKSZTAŁCONY",  "ODTWORZONY"]
        subtitles   = ["obraz wejściowy", "po scrambligu", "po unscramblingu"]
        border_cols = PANEL_COLORS

        self.img_labels   = []
        self.img_canvases = []

        for i, (title, subtitle, bcolor) in enumerate(zip(titles, subtitles, border_cols)):
            # Zewnętrzna ramka (kolor bordera)
            outer = tk.Frame(parent, bg=bcolor, bd=0)
            outer.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

            # Wewnętrzna ramka
            inner = tk.Frame(outer, bg=PANEL_BG, bd=0)
            inner.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

            # Pasek tytułu
            title_bar = tk.Frame(inner, bg=bcolor, height=32)
            title_bar.pack(fill=tk.X)
            title_bar.pack_propagate(False)

            tk.Label(
                title_bar, text=title,
                font=("Courier New", 9, "bold"),
                fg=PANEL_BG, bg=bcolor
            ).pack(side=tk.LEFT, padx=10, pady=6)

            tk.Label(
                title_bar, text=subtitle,
                font=("Courier New", 7),
                fg=PANEL_BG, bg=bcolor
            ).pack(side=tk.RIGHT, padx=10, pady=8)

            # Canvas obrazu
            canvas = tk.Canvas(inner, bg="#08080f", highlightthickness=0)
            canvas.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

            lbl = tk.Label(
                canvas, text="— brak obrazu —",
                font=("Courier New", 9),
                fg=THEME["text_muted"], bg="#08080f"
            )
            lbl.place(relx=0.5, rely=0.5, anchor="center")

            self.img_canvases.append(canvas)
            self.img_labels.append(lbl)

            # Label metryki pod obrazem
            metric_lbl = tk.Label(
                inner, text="",
                font=("Courier New", 8),
                fg=bcolor, bg=PANEL_BG
            )
            metric_lbl.pack(pady=(2, 4))
            # Zapisz referencję
            if not hasattr(self, "panel_metric_labels"):
                self.panel_metric_labels = []
            self.panel_metric_labels.append(metric_lbl)

    # ----------------------------------------------------------
    # METRYKI
    # ----------------------------------------------------------

    def _build_metrics(self, parent):
        # Header
        hdr = tk.Frame(parent, bg=THEME["bg_panel"])
        hdr.pack(fill=tk.X, padx=14, pady=(8, 2))

        tk.Label(
            hdr, text="METRYKI ANALITYCZNE",
            font=("Courier New", 9, "bold"),
            fg=THEME["accent"], bg=THEME["bg_panel"]
        ).pack(side=tk.LEFT)

        tk.Frame(hdr, bg=THEME["border"], height=1).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0), pady=6
        )

        self.metrics_text = tk.Text(
            parent, height=5,
            font=("Courier New", 9),
            bg="#08080f", fg=THEME["text_main"],
            insertbackground="white",
            relief=tk.FLAT, bd=0,
            state=tk.DISABLED,
            padx=10, pady=6,
            selectbackground=THEME["accent2"],
        )
        self.metrics_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 8))

        # Tagi kolorów
        self.metrics_text.tag_configure("label",   foreground=THEME["text_dim"])
        self.metrics_text.tag_configure("good",    foreground=THEME["green"])
        self.metrics_text.tag_configure("bad",     foreground=THEME["red"])
        self.metrics_text.tag_configure("neutral", foreground=THEME["yellow"])
        self.metrics_text.tag_configure("header",  foreground="#ffffff",
                                         font=("Courier New", 9, "bold"))
        self.metrics_text.tag_configure("accent",  foreground=THEME["accent"])

    # ----------------------------------------------------------
    # LOGIKA
    # ----------------------------------------------------------

    def _on_stage_change(self):
        infos = {
            1: "Przesunięcia cykliczne wierszy\ni kolumn. Klucz: shift (int).\nSłabość: zachowuje lokalne wzorce.",
            2: "Permutacja Fisher-Yates.\nKlucz: seed (int).\nP(i) i P⁻¹ są jawnie obliczane.",
            3: "Permutacja + XOR pseudolosowy.\nKlucz: seed.\nf(p,k) = p XOR K[i]  (samoodwrotne).",
        }
        self.stage_info.config(text=infos.get(self.stage_var.get(), ""))

    def _load_image(self):
        path = filedialog.askopenfilename(
            filetypes=[("Obrazy", "*.png *.jpg *.jpeg *.bmp *.tiff"), ("Wszystkie", "*.*")]
        )
        if not path:
            return

        img = Image.open(path).convert("RGB")
        max_dim = 512
        if max(img.size) > max_dim:
            ratio = max_dim / max(img.size)
            new_size = (int(img.width * ratio), int(img.height * ratio))
            img = img.resize(new_size, Image.LANCZOS)

        self.original_array  = np.array(img)
        self.scrambled_array = None
        self.recovered_array = None

        self._display_image(self.original_array, 0)
        self._clear_image(1)
        self._clear_image(2)
        self._update_metrics_plain("")
        self._set_panel_metric(0, f"{img.size[0]} × {img.size[1]} px")
        self._set_panel_metric(1, "")
        self._set_panel_metric(2, "")
        self._set_status(f"Wczytano: {os.path.basename(path)}  ·  {img.size[0]}×{img.size[1]} px")

    def _get_key(self):
        if self.use_wrong_key.get():
            return int(self.wrong_key_var.get())
        return int(self.key_var.get())

    def _scramble(self):
        if self.original_array is None:
            messagebox.showerror("Błąd", "Najpierw wczytaj obraz!")
            return
        try:
            key   = self._get_key()
            stage = self.stage_var.get()

            if stage == 1:
                self.scrambled_array = self.naive.scramble(self.original_array, key)
            elif stage == 2:
                self.scrambled_array = self.permuter.scramble(self.original_array, key)
                n  = self.original_array.shape[0] * self.original_array.shape[1]
                ok = self.permuter.verify_inverse(n, key)
                self.verify_label.config(
                    text=f"P⁻¹(P(i))=i  {'✓ OK' if ok else '✗ BŁĄD'}",
                    fg=THEME["green"] if ok else THEME["red"]
                )
            else:
                self.scrambled_array = self.hybrid.scramble(self.original_array, key)
                self.verify_label.config(text="")

            self._display_image(self.scrambled_array, 1)
            self._clear_image(2)
            self.recovered_array = None
            self._auto_metrics()
            self._set_status(f"Scramble  ·  Etap {stage}  ·  klucz={key}")

        except ValueError as e:
            messagebox.showerror("Błąd klucza", f"Klucz musi być liczbą całkowitą.\n{e}")

    def _unscramble(self):
        if self.scrambled_array is None:
            messagebox.showerror("Błąd", "Najpierw wykonaj Scramble!")
            return
        try:
            key   = self._get_key()
            stage = self.stage_var.get()

            if stage == 1:
                self.recovered_array = self.naive.unscramble(self.scrambled_array, key)
            elif stage == 2:
                self.recovered_array = self.permuter.unscramble(self.scrambled_array, key)
            else:
                self.recovered_array = self.hybrid.unscramble(self.scrambled_array, key)

            self._display_image(self.recovered_array, 2)
            self._auto_metrics()
            self._set_status(f"Unscramble  ·  Etap {stage}  ·  klucz={key}")

        except ValueError as e:
            messagebox.showerror("Błąd klucza", f"Klucz musi być liczbą całkowitą.\n{e}")

    def _auto_metrics(self):
        self.metrics_text.config(state=tk.NORMAL)
        self.metrics_text.delete("1.0", tk.END)

        def ins(text, tag=None):
            if tag:
                self.metrics_text.insert(tk.END, text, tag)
            else:
                self.metrics_text.insert(tk.END, text)

        if self.original_array is not None:
            c_orig = compute_correlation(self.original_array)
            ins("Korelacja oryginału:         ", "label")
            ins(f"{c_orig:+.4f}\n", "accent")
            self._set_panel_metric(0, f"korelacja: {c_orig:+.4f}")

        if self.scrambled_array is not None:
            c_scr = compute_correlation(self.scrambled_array)
            quality = "good" if abs(c_scr) < 0.05 else ("neutral" if abs(c_scr) < 0.3 else "bad")
            ins("Korelacja przekształconego:  ", "label")
            ins(f"{c_scr:+.4f}", quality)
            ins(f"  ({'dobry scrambling' if abs(c_scr) < 0.1 else 'słaby scrambling'})\n", "label")
            self._set_panel_metric(1, f"korelacja: {c_scr:+.4f}")

        if self.original_array is not None and self.recovered_array is not None:
            diff = compute_pixel_difference(self.original_array, self.recovered_array)
            psnr = compute_psnr(self.original_array, self.recovered_array)
            ins("Różnica pikselowa (odtw.):   ", "label")
            diff_tag = "good" if diff < 0.01 else "bad"
            ins(f"{diff:.4f}\n", diff_tag)
            psnr_str = f"{psnr:.2f} dB" if psnr != float('inf') else "∞  (identyczne)"
            ins("PSNR:                        ", "label")
            ins(f"{psnr_str}\n", "good" if psnr > 60 or psnr == float('inf') else "neutral")
            self._set_panel_metric(2, f"PSNR: {psnr_str}")

        self.metrics_text.config(state=tk.DISABLED)

    def _run_analysis(self):
        if self.original_array is None:
            messagebox.showerror("Błąd", "Wczytaj obraz przed analizą!")
            return

        try:
            key       = int(self.key_var.get())
            wrong_key = int(self.wrong_key_var.get())
        except ValueError:
            messagebox.showerror("Błąd", "Klucze muszą być liczbami całkowitymi!")
            return

        stage = self.stage_var.get()

        if stage == 1:
            scr            = self.naive.scramble(self.original_array, key)
            rec            = self.naive.unscramble(scr, key)
            scr_wrong_key  = self.naive.unscramble(scr, wrong_key)
        elif stage == 2:
            scr            = self.permuter.scramble(self.original_array, key)
            rec            = self.permuter.unscramble(scr, key)
            scr_wrong_key  = self.permuter.unscramble(scr, wrong_key)
        else:
            scr            = self.hybrid.scramble(self.original_array, key)
            rec            = self.hybrid.unscramble(scr, key)
            scr_wrong_key  = self.hybrid.unscramble(scr, wrong_key)

        c_orig      = compute_correlation(self.original_array)
        c_scr       = compute_correlation(scr)
        psnr_ok     = compute_psnr(self.original_array, rec)
        diff_ok     = compute_pixel_difference(self.original_array, rec)
        diff_wrong  = compute_pixel_difference(self.original_array, scr_wrong_key)

        self.metrics_text.config(state=tk.NORMAL)
        self.metrics_text.delete("1.0", tk.END)

        def ins(text, tag=None):
            if tag:
                self.metrics_text.insert(tk.END, text, tag)
            else:
                self.metrics_text.insert(tk.END, text)

        ins(f"=== ANALIZA ETAPU {stage} ===\n", "header")
        ins("Korelacja oryginału:              ", "label");  ins(f"{c_orig:+.4f}\n", "accent")
        ins("Korelacja przekształconego:       ", "label");  ins(f"{c_scr:+.4f}\n",  "good" if abs(c_scr) < 0.1 else "bad")
        ins("Redukcja korelacji:               ", "label");  ins(f"{abs(c_orig - c_scr):.4f}\n", "neutral")
        psnr_str = f"{psnr_ok:.2f} dB" if psnr_ok != float('inf') else "∞"
        ins(f"PSNR poprawny klucz ({key}):     ", "label");  ins(f"{psnr_str}\n", "good")
        ins(f"Różnica pikselowa (poprawny):     ", "label");  ins(f"{diff_ok:.6f}\n", "good" if diff_ok < 0.01 else "bad")
        ins(f"Różnica pikselowa (błędny {wrong_key}): ", "label")
        ins(f"{diff_wrong:.2f}  ", "bad" if diff_wrong > 20 else "neutral")
        ins(f"({'znacząco' if diff_wrong > 20 else 'minimalnie'} inny)\n", "label")

        self.metrics_text.config(state=tk.DISABLED)
        self._set_status(f"Analiza zakończona  ·  Etap {stage}")
        messagebox.showinfo("Analiza zakończona", "Metryki zaktualizowane.\nSprawdź panel dolny.")

    # ----------------------------------------------------------
    # WYŚWIETLANIE OBRAZÓW
    # ----------------------------------------------------------

    def _display_image(self, arr: np.ndarray, panel_idx: int):
        canvas = self.img_canvases[panel_idx]
        canvas.update_idletasks()
        cw = canvas.winfo_width()  or 360
        ch = canvas.winfo_height() or 360

        img = Image.fromarray(arr.astype(np.uint8))
        img.thumbnail((cw - 8, ch - 8), Image.LANCZOS)

        photo = ImageTk.PhotoImage(img)
        canvas.delete("all")
        canvas.create_image(cw // 2, ch // 2, anchor="center", image=photo)
        canvas.image = photo
        self.img_labels[panel_idx].place_forget()

    def _clear_image(self, panel_idx: int):
        canvas = self.img_canvases[panel_idx]
        canvas.delete("all")
        lbl = self.img_labels[panel_idx]
        lbl.place(relx=0.5, rely=0.5, anchor="center")

    def _set_panel_metric(self, idx: int, text: str):
        if hasattr(self, "panel_metric_labels") and idx < len(self.panel_metric_labels):
            self.panel_metric_labels[idx].config(text=text)

    def _set_status(self, text: str):
        if hasattr(self, "status_var"):
            self.status_var.set(text)

    def _update_metrics_plain(self, text: str):
        self.metrics_text.config(state=tk.NORMAL)
        self.metrics_text.delete("1.0", tk.END)
        self.metrics_text.insert(tk.END, text)
        self.metrics_text.config(state=tk.DISABLED)

    # ----------------------------------------------------------
    # ZAPIS
    # ----------------------------------------------------------

    def _save_results(self):
        if self.original_array is None:
            messagebox.showerror("Błąd", "Brak danych do zapisu!")
            return

        dir_path = filedialog.askdirectory(title="Wybierz folder zapisu")
        if not dir_path:
            return

        saved = []
        p = os.path.join(dir_path, "original.png")
        Image.fromarray(self.original_array).save(p)
        saved.append("original.png")

        if self.scrambled_array is not None:
            name = f"scrambled_stage{self.stage_var.get()}.png"
            Image.fromarray(self.scrambled_array.astype(np.uint8)).save(os.path.join(dir_path, name))
            saved.append(name)

        if self.recovered_array is not None:
            name = f"recovered_stage{self.stage_var.get()}.png"
            Image.fromarray(self.recovered_array.astype(np.uint8)).save(os.path.join(dir_path, name))
            saved.append(name)

        self._set_status(f"Zapisano {len(saved)} plik(ów) do: {dir_path}")
        messagebox.showinfo("Zapisano", "Pliki zapisane:\n" + "\n".join(saved))


# ============================================================
# PUNKT WEJŚCIA
# ============================================================

def main():
    root = tk.Tk()
    app  = ImageScrambleGUI(root)

    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TFrame",     background=THEME["bg_dark"])
    style.configure("TSeparator", background=THEME["border"])

    root.mainloop()


if __name__ == "__main__":
    main()
