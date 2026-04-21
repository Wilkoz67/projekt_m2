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
        """
        Przekształcenie: każdy wiersz i przesuwamy o (i * key) % width,
        każda kolumna j przesuwana o (j * key) % height.
        """
        arr = img_array.copy()
        h, w = arr.shape[:2]

        # Przesunięcie wierszy
        for i in range(h):
            shift = (i * key) % w
            arr[i] = np.roll(arr[i], shift, axis=0)

        # Przesunięcie kolumn
        result = arr.copy()
        for j in range(w):
            shift = (j * key) % h
            result[:, j] = np.roll(arr[:, j], shift, axis=0)

        return result

    def unscramble(self, img_array: np.ndarray, key: int) -> np.ndarray:
        """
        Odwrócenie: stosujemy przesunięcia w odwrotnej kolejności z negacją.
        """
        arr = img_array.copy()
        h, w = arr.shape[:2]

        # Odwróć przesunięcie kolumn (odwrotna kolejność)
        result = arr.copy()
        for j in range(w):
            shift = (j * key) % h
            result[:, j] = np.roll(arr[:, j], -shift, axis=0)

        # Odwróć przesunięcie wierszy
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
    Funkcja P: {0..N-1} -> {0..N-1}
    Funkcja P^-1: odwrócenie permutacji.
    Wartości pikseli NIE są zmieniane, tylko ich pozycje.
    """

    def _generate_permutation(self, n: int, seed: int):
        """
        Generuje permutację Fisher-Yates dla n elementów z danym seedem.
        Zwraca tablicę permutacji P oraz jej odwrotność P_inv.
        """
        rng = np.random.default_rng(seed)
        perm = np.arange(n)
        rng.shuffle(perm)

        # Odwrotność permutacji: P_inv[P[i]] = i
        perm_inv = np.empty_like(perm)
        perm_inv[perm] = np.arange(n)

        return perm, perm_inv

    def scramble(self, img_array: np.ndarray, seed: int) -> np.ndarray:
        """
        Stosuje permutację P do wszystkich pikseli (spłaszczony obraz).
        """
        h, w = img_array.shape[:2]
        n = h * w
        channels = img_array.shape[2] if img_array.ndim == 3 else 1

        flat = img_array.reshape(n, -1) if channels > 1 else img_array.reshape(n)
        perm, _ = self._generate_permutation(n, seed)
        scrambled_flat = flat[perm]

        return scrambled_flat.reshape(img_array.shape)

    def unscramble(self, img_array: np.ndarray, seed: int) -> np.ndarray:
        """
        Stosuje permutację odwrotną P^-1.
        """
        h, w = img_array.shape[:2]
        n = h * w
        channels = img_array.shape[2] if img_array.ndim == 3 else 1

        flat = img_array.reshape(n, -1) if channels > 1 else img_array.reshape(n)
        _, perm_inv = self._generate_permutation(n, seed)
        unscrambled_flat = flat[perm_inv]

        return unscrambled_flat.reshape(img_array.shape)

    def verify_inverse(self, n: int, seed: int) -> bool:
        """Weryfikuje: P^-1(P(i)) = i dla wszystkich i."""
        perm, perm_inv = self._generate_permutation(n, seed)
        identity = perm_inv[perm]
        return np.all(identity == np.arange(n))


# ============================================================
# ETAP 3: Mechanizm wzmacniający - Substytucja deterministyczna
# ============================================================

class HybridScrambler:
    """
    Etap 3: Hybryda - Permutacja + Substytucja deterministyczna.
    Klasa C: Hybryda (permutacja + substytucja).

    Kolejność operacji:
      Scramble: permutacja -> substytucja (XOR z pseudolosowym kluczem)
      Unscramble: odwrotna substytucja -> odwrotna permutacja

    Substytucja: f(p, k) = p XOR K[i]
    Odwrotność:  f^-1(p, k) = p XOR K[i]   (XOR jest samoodwrotne)
    """

    def __init__(self):
        self.permuter = KeyedPermutationScrambler()

    def _generate_xor_mask(self, shape, seed: int) -> np.ndarray:
        """
        Generuje pseudolosową maskę XOR o danym kształcie.
        Każdy piksel/kanał XOR-owany z inną wartością.
        """
        rng = np.random.default_rng(seed + 99999)  # inny seed niż permutacja
        mask = rng.integers(0, 256, size=shape, dtype=np.uint8)
        return mask

    def scramble(self, img_array: np.ndarray, seed: int) -> np.ndarray:
        """
        1. Permutacja pikseli (Etap 2)
        2. Substytucja XOR z maską pseudolosową
        """
        # Krok 1: Permutacja
        permuted = self.permuter.scramble(img_array, seed)

        # Krok 2: Substytucja XOR
        mask = self._generate_xor_mask(permuted.shape, seed)
        result = (permuted.astype(np.int32) ^ mask.astype(np.int32)).astype(np.uint8)

        return result

    def unscramble(self, img_array: np.ndarray, seed: int) -> np.ndarray:
        """
        Odwrócenie w kolejności odwrotnej:
        1. Odwrotna substytucja XOR (XOR z tą samą maską)
        2. Odwrotna permutacja
        """
        # Krok 1: Odwrotna substytucja XOR (XOR jest samoodwrotne)
        mask = self._generate_xor_mask(img_array.shape, seed)
        desubstituted = (img_array.astype(np.int32) ^ mask.astype(np.int32)).astype(np.uint8)

        # Krok 2: Odwrotna permutacja
        result = self.permuter.unscramble(desubstituted, seed)

        return result


# ============================================================
# METRYKI ANALITYCZNE
# ============================================================

def compute_correlation(img_array: np.ndarray) -> float:
    """
    Korelacja sąsiednich pikseli poziomo.
    Wartość bliska 1 -> silna korelacja (obraz naturalny).
    Wartość bliska 0 -> brak korelacji (dobry scrambling).
    """
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
    """
    Średnia różnica pikselowa między dwoma obrazami (0-255).
    """
    diff = np.abs(img1.astype(float) - img2.astype(float))
    return float(np.mean(diff))


def compute_psnr(original: np.ndarray, recovered: np.ndarray) -> float:
    """
    PSNR (Peak Signal-to-Noise Ratio) w dB.
    Inf -> identyczne obrazy.
    """
    mse = np.mean((original.astype(float) - recovered.astype(float)) ** 2)
    if mse == 0:
        return float('inf')
    return 20 * math.log10(255.0 / math.sqrt(mse))


# ============================================================
# GUI
# ============================================================

class ImageScrambleGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Projekt M-II – Chaotyczne przekształcanie obrazu cyfrowego")
        self.root.configure(bg="#0f0f1a")
        self.root.geometry("1400x900")
        self.root.minsize(1100, 750)

        # Dane
        self.original_array = None
        self.scrambled_array = None
        self.recovered_array = None

        # Algorytmy
        self.naive = NaiveScrambler()
        self.permuter = KeyedPermutationScrambler()
        self.hybrid = HybridScrambler()

        self._build_ui()

    def _build_ui(self):
        # ---- Pasek górny ----
        top = tk.Frame(self.root, bg="#0d0d1f", height=60)
        top.pack(fill=tk.X)
        tk.Label(
            top,
            text="PROJEKT M-II  ·  Chaotyczne przekształcanie obrazu",
            font=("Courier New", 14, "bold"),
            fg="#00ffcc", bg="#0d0d1f"
        ).pack(side=tk.LEFT, padx=20, pady=15)

        # ---- Główny układ ----
        main = tk.Frame(self.root, bg="#0f0f1a")
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Lewa kolumna: panel sterowania
        ctrl = tk.Frame(main, bg="#13132a", width=280, relief=tk.FLAT, bd=0)
        ctrl.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8), pady=0)
        ctrl.pack_propagate(False)
        self._build_controls(ctrl)

        # Prawa kolumna: obrazy + metryki
        right = tk.Frame(main, bg="#0f0f1a")
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Obrazy
        img_frame = tk.Frame(right, bg="#0f0f1a")
        img_frame.pack(fill=tk.BOTH, expand=True)
        self._build_image_panels(img_frame)

        # Metryki
        metrics_frame = tk.Frame(right, bg="#13132a", height=130)
        metrics_frame.pack(fill=tk.X, pady=(8, 0))
        metrics_frame.pack_propagate(False)
        self._build_metrics(metrics_frame)

    def _build_controls(self, parent):
        tk.Label(parent, text="STEROWANIE", font=("Courier New", 10, "bold"),
                 fg="#00ffcc", bg="#13132a").pack(pady=(15, 5), padx=15, anchor="w")
        ttk.Separator(parent, orient="horizontal").pack(fill=tk.X, padx=10, pady=5)

        # Wczytaj obraz
        self._btn(parent, "📂  Wczytaj obraz", self._load_image)

        ttk.Separator(parent, orient="horizontal").pack(fill=tk.X, padx=10, pady=8)

        # Etap
        tk.Label(parent, text="Etap:", font=("Courier New", 9),
                 fg="#aaaacc", bg="#13132a").pack(padx=15, anchor="w")
        self.stage_var = tk.IntVar(value=1)
        for val, label in [(1, "Etap 1  –  Naiwny scrambling"),
                            (2, "Etap 2  –  Czysta permutacja"),
                            (3, "Etap 3  –  Hybrydowy")]:
            rb = tk.Radiobutton(
                parent, text=label, variable=self.stage_var, value=val,
                font=("Courier New", 9), fg="#ccccee", bg="#13132a",
                selectcolor="#1e1e3f", activebackground="#13132a",
                activeforeground="#00ffcc", command=self._on_stage_change
            )
            rb.pack(padx=20, anchor="w", pady=2)

        ttk.Separator(parent, orient="horizontal").pack(fill=tk.X, padx=10, pady=8)

        # Klucz
        tk.Label(parent, text="Klucz (seed / shift):", font=("Courier New", 9),
                 fg="#aaaacc", bg="#13132a").pack(padx=15, anchor="w")
        self.key_var = tk.StringVar(value="42")
        key_entry = tk.Entry(parent, textvariable=self.key_var,
                             font=("Courier New", 12), bg="#1a1a35",
                             fg="#00ffcc", insertbackground="#00ffcc",
                             relief=tk.FLAT, bd=0)
        key_entry.pack(padx=15, pady=(3, 10), fill=tk.X)

        # Błędny klucz
        tk.Label(parent, text="Błędny klucz (test):", font=("Courier New", 9),
                 fg="#aaaacc", bg="#13132a").pack(padx=15, anchor="w")
        self.wrong_key_var = tk.StringVar(value="43")
        wrong_entry = tk.Entry(parent, textvariable=self.wrong_key_var,
                               font=("Courier New", 12), bg="#1a1a35",
                               fg="#ff6666", insertbackground="#ff6666",
                               relief=tk.FLAT, bd=0)
        wrong_entry.pack(padx=15, pady=(3, 10), fill=tk.X)

        # Przełącznik klucza
        self.use_wrong_key = tk.BooleanVar(value=False)
        cb = tk.Checkbutton(
            parent, text="Użyj błędnego klucza",
            variable=self.use_wrong_key,
            font=("Courier New", 9), fg="#ff9966", bg="#13132a",
            selectcolor="#1e1e3f", activebackground="#13132a"
        )
        cb.pack(padx=15, anchor="w", pady=(0, 8))

        ttk.Separator(parent, orient="horizontal").pack(fill=tk.X, padx=10, pady=5)

        # Przyciski
        self._btn(parent, "🔀  SCRAMBLE", self._scramble, color="#00cc88")
        self._btn(parent, "🔁  UNSCRAMBLE", self._unscramble, color="#0088ff")
        self._btn(parent, "📊  Analiza + metryki", self._run_analysis, color="#aa44ff")

        ttk.Separator(parent, orient="horizontal").pack(fill=tk.X, padx=10, pady=8)
        self._btn(parent, "💾  Zapisz wyniki", self._save_results, color="#666688")

        # Etap 2: weryfikacja
        self.verify_label = tk.Label(parent, text="", font=("Courier New", 8),
                                      fg="#00ff88", bg="#13132a", wraplength=240)
        self.verify_label.pack(padx=10, pady=5)

        # Informacja o etapie
        self.stage_info = tk.Label(parent, text="", font=("Courier New", 8),
                                    fg="#8888aa", bg="#13132a", wraplength=240,
                                    justify=tk.LEFT)
        self.stage_info.pack(padx=10, pady=5, anchor="w")
        self._on_stage_change()

    def _btn(self, parent, text, cmd, color="#334466"):
        btn = tk.Button(
            parent, text=text, command=cmd,
            font=("Courier New", 9, "bold"),
            fg="white", bg=color, activebackground="#ffffff",
            activeforeground="#000000", relief=tk.FLAT, bd=0,
            padx=10, pady=8, cursor="hand2"
        )
        btn.pack(padx=15, pady=3, fill=tk.X)
        return btn

    def _build_image_panels(self, parent):
        titles = ["ORYGINAŁ", "PRZEKSZTAŁCONY", "ODTWORZONY"]
        self.img_labels = []
        self.img_canvases = []

        for i, title in enumerate(titles):
            frame = tk.Frame(parent, bg="#13132a")
            frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4, pady=4)

            tk.Label(frame, text=title, font=("Courier New", 9, "bold"),
                     fg="#00ffcc", bg="#13132a").pack(pady=(8, 4))

            canvas = tk.Canvas(frame, bg="#0a0a1a", highlightthickness=0)
            canvas.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0, 6))

            lbl = tk.Label(canvas, text="Brak obrazu", font=("Courier New", 9),
                           fg="#445566", bg="#0a0a1a")
            lbl.place(relx=0.5, rely=0.5, anchor="center")

            self.img_canvases.append(canvas)
            self.img_labels.append(lbl)

    def _build_metrics(self, parent):
        tk.Label(parent, text="METRYKI ANALITYCZNE", font=("Courier New", 9, "bold"),
                 fg="#00ffcc", bg="#13132a").pack(anchor="w", padx=15, pady=(10, 3))

        self.metrics_text = tk.Text(
            parent, height=5, font=("Courier New", 9),
            bg="#0a0a1a", fg="#aaddff", insertbackground="white",
            relief=tk.FLAT, bd=0, state=tk.DISABLED
        )
        self.metrics_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 8))

    def _on_stage_change(self):
        infos = {
            1: "Etap 1: Przesunięcia cykliczne wierszy i kolumn.\nKlucz: shift (liczba całkowita).\nSłabość: zachowuje lokalne wzorce.",
            2: "Etap 2: Permutacja Fisher-Yates.\nKlucz: seed (int).\nP(i) i P^-1 są jawnie obliczane.",
            3: "Etap 3: Permutacja + XOR pseudolosowy.\nKlucz: seed.\nf(p,k)=p XOR K[i], odwrotność = ta sama.",
        }
        self.stage_info.config(text=infos.get(self.stage_var.get(), ""))

    def _load_image(self):
        path = filedialog.askopenfilename(
            filetypes=[("Obrazy", "*.png *.jpg *.jpeg *.bmp *.tiff"), ("Wszystkie", "*.*")]
        )
        if not path:
            return

        img = Image.open(path).convert("RGB")
        # Ograniczenie rozmiaru dla wydajności
        max_dim = 512
        if max(img.size) > max_dim:
            ratio = max_dim / max(img.size)
            new_size = (int(img.width * ratio), int(img.height * ratio))
            img = img.resize(new_size, Image.LANCZOS)

        self.original_array = np.array(img)
        self.scrambled_array = None
        self.recovered_array = None

        self._display_image(self.original_array, 0)
        self._clear_image(1)
        self._clear_image(2)
        self._update_metrics("")
        messagebox.showinfo("Wczytano", f"Obraz załadowany: {img.size[0]}×{img.size[1]} px")

    def _get_key(self):
        if self.use_wrong_key.get():
            return int(self.wrong_key_var.get())
        return int(self.key_var.get())

    def _scramble(self):
        if self.original_array is None:
            messagebox.showerror("Błąd", "Najpierw wczytaj obraz!")
            return
        try:
            key = self._get_key()
            stage = self.stage_var.get()

            if stage == 1:
                self.scrambled_array = self.naive.scramble(self.original_array, key)
            elif stage == 2:
                self.scrambled_array = self.permuter.scramble(self.original_array, key)
                # Weryfikacja P^-1(P(i)) = i
                n = self.original_array.shape[0] * self.original_array.shape[1]
                ok = self.permuter.verify_inverse(n, key)
                self.verify_label.config(
                    text=f"✓ P^-1(P(i))=i verified: {'OK' if ok else 'BŁĄD'}",
                    fg="#00ff88" if ok else "#ff4444"
                )
            else:
                self.scrambled_array = self.hybrid.scramble(self.original_array, key)
                self.verify_label.config(text="")

            self._display_image(self.scrambled_array, 1)
            self._clear_image(2)
            self.recovered_array = None
            self._auto_metrics()

        except ValueError as e:
            messagebox.showerror("Błąd klucza", f"Klucz musi być liczbą całkowitą.\n{e}")

    def _unscramble(self):
        if self.scrambled_array is None:
            messagebox.showerror("Błąd", "Najpierw wykonaj Scramble!")
            return
        try:
            key = self._get_key()
            stage = self.stage_var.get()

            if stage == 1:
                self.recovered_array = self.naive.unscramble(self.scrambled_array, key)
            elif stage == 2:
                self.recovered_array = self.permuter.unscramble(self.scrambled_array, key)
            else:
                self.recovered_array = self.hybrid.unscramble(self.scrambled_array, key)

            self._display_image(self.recovered_array, 2)
            self._auto_metrics()

        except ValueError as e:
            messagebox.showerror("Błąd klucza", f"Klucz musi być liczbą całkowitą.\n{e}")

    def _auto_metrics(self):
        lines = []
        if self.original_array is not None:
            c_orig = compute_correlation(self.original_array)
            lines.append(f"Korelacja oryginału:          {c_orig:+.4f}")
        if self.scrambled_array is not None:
            c_scr = compute_correlation(self.scrambled_array)
            lines.append(f"Korelacja przekształconego:   {c_scr:+.4f}")
        if self.original_array is not None and self.recovered_array is not None:
            diff = compute_pixel_difference(self.original_array, self.recovered_array)
            psnr = compute_psnr(self.original_array, self.recovered_array)
            lines.append(f"Śr. różnica pikselowa (odtworzony vs oryginał): {diff:.4f}")
            psnr_str = f"{psnr:.2f} dB" if psnr != float('inf') else "∞ (identyczne)"
            lines.append(f"PSNR: {psnr_str}")
        self._update_metrics("\n".join(lines))

    def _run_analysis(self):
        if self.original_array is None:
            messagebox.showerror("Błąd", "Wczytaj obraz przed analizą!")
            return

        try:
            key = int(self.key_var.get())
            wrong_key = int(self.wrong_key_var.get())
        except ValueError:
            messagebox.showerror("Błąd", "Klucze muszą być liczbami całkowitymi!")
            return

        stage = self.stage_var.get()
        lines = [f"=== ANALIZA ETAPU {stage} ===\n"]

        # Korelacja oryginału
        c_orig = compute_correlation(self.original_array)
        lines.append(f"Korelacja oryginału:               {c_orig:+.4f}")

        # Scramble poprawnym kluczem
        if stage == 1:
            scr = self.naive.scramble(self.original_array, key)
            rec = self.naive.unscramble(scr, key)
            scr_wrong_key = self.naive.unscramble(scr, wrong_key)
        elif stage == 2:
            scr = self.permuter.scramble(self.original_array, key)
            rec = self.permuter.unscramble(scr, key)
            scr_wrong_key = self.permuter.unscramble(scr, wrong_key)
        else:
            scr = self.hybrid.scramble(self.original_array, key)
            rec = self.hybrid.unscramble(scr, key)
            scr_wrong_key = self.hybrid.unscramble(scr, wrong_key)

        c_scr = compute_correlation(scr)
        lines.append(f"Korelacja przekształconego:        {c_scr:+.4f}")
        lines.append(f"Redukcja korelacji:                {abs(c_orig - c_scr):.4f}")

        psnr_correct = compute_psnr(self.original_array, rec)
        psnr_str = f"{psnr_correct:.2f} dB" if psnr_correct != float('inf') else "∞"
        lines.append(f"\nPSNR (poprawny klucz {key}):      {psnr_str}")

        diff_correct = compute_pixel_difference(self.original_array, rec)
        lines.append(f"Średnia różnica pikselowa:         {diff_correct:.6f}")

        diff_wrong = compute_pixel_difference(self.original_array, scr_wrong_key)
        lines.append(f"\nŚr. różnica (błędny klucz {wrong_key}): {diff_wrong:.2f}")
        lines.append(f"Błędny klucz: obraz {'znacząco' if diff_wrong > 20 else 'minimalnie'} inny")

        self._update_metrics("\n".join(lines))
        messagebox.showinfo("Analiza zakończona", "Metryki zaktualizowane.\nSprawdź panel dolny.")

    def _display_image(self, arr: np.ndarray, panel_idx: int):
        canvas = self.img_canvases[panel_idx]
        canvas.update_idletasks()
        cw = canvas.winfo_width() or 350
        ch = canvas.winfo_height() or 350

        img = Image.fromarray(arr.astype(np.uint8))
        img.thumbnail((cw - 10, ch - 10), Image.LANCZOS)

        photo = ImageTk.PhotoImage(img)
        canvas.delete("all")
        canvas.create_image(cw // 2, ch // 2, anchor="center", image=photo)
        canvas.image = photo  # zapobieganie GC
        self.img_labels[panel_idx].place_forget()

    def _clear_image(self, panel_idx: int):
        canvas = self.img_canvases[panel_idx]
        canvas.delete("all")
        lbl = self.img_labels[panel_idx]
        lbl.place(relx=0.5, rely=0.5, anchor="center")

    def _update_metrics(self, text: str):
        self.metrics_text.config(state=tk.NORMAL)
        self.metrics_text.delete("1.0", tk.END)
        self.metrics_text.insert(tk.END, text)
        self.metrics_text.config(state=tk.DISABLED)

    def _save_results(self):
        if self.original_array is None:
            messagebox.showerror("Błąd", "Brak danych do zapisu!")
            return

        dir_path = filedialog.askdirectory(title="Wybierz folder zapisu")
        if not dir_path:
            return

        saved = []
        if self.original_array is not None:
            p = os.path.join(dir_path, "original.png")
            Image.fromarray(self.original_array).save(p)
            saved.append("original.png")

        if self.scrambled_array is not None:
            p = os.path.join(dir_path, f"scrambled_stage{self.stage_var.get()}.png")
            Image.fromarray(self.scrambled_array.astype(np.uint8)).save(p)
            saved.append(f"scrambled_stage{self.stage_var.get()}.png")

        if self.recovered_array is not None:
            p = os.path.join(dir_path, f"recovered_stage{self.stage_var.get()}.png")
            Image.fromarray(self.recovered_array.astype(np.uint8)).save(p)
            saved.append(f"recovered_stage{self.stage_var.get()}.png")

        messagebox.showinfo("Zapisano", f"Pliki zapisane:\n" + "\n".join(saved))


# ============================================================
# PUNKT WEJŚCIA
# ============================================================

def main():
    root = tk.Tk()
    app = ImageScrambleGUI(root)

    # Styl ttk
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TFrame", background="#0f0f1a")
    style.configure("TSeparator", background="#2a2a4a")

    root.mainloop()


if __name__ == "__main__":
    main()
