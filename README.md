# Projekt M-II: Chaotyczne Przekształcanie Obrazu Cyfrowego

> Implementacja algorytmów permutacji, substytucji i chaosu w przetwarzaniu obrazu — z graficznym interfejsem użytkownika (GUI).

---

## O projekcie

Projekt demonstruje trzy etapy "scramblingu" (zaburzania) obrazu cyfrowego:

| Etap | Metoda | Klucz |
|------|--------|-------|
| **1 – Naiwny scrambling** | Cykliczne przesunięcia (`np.roll`) wierszy i kolumn | Liczba całkowita (shift) |
| **2 – Czysta permutacja** | Fisher-Yates shuffle z odwrotną permutacją P⁻¹ | Seed losowy |
| **3 – Hybryda** | Permutacja + substytucja XOR z maską pseudolosową | Seed losowy |

Każdy etap posiada funkcję `scramble` i `unscramble` — możliwe jest pełne odtworzenie oryginalnego obrazu ze zniszczonej wersji przy użyciu tego samego klucza.

---

## Technologie

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python&logoColor=white)
![NumPy](https://img.shields.io/badge/NumPy-1.24%2B-013243?logo=numpy)
![Pillow](https://img.shields.io/badge/Pillow-10.0%2B-yellow)
![Matplotlib](https://img.shields.io/badge/Matplotlib-3.7%2B-orange)
![Tkinter](https://img.shields.io/badge/GUI-Tkinter-lightgrey)

- **Język:** Python 3.9+
- **GUI:** Tkinter (wbudowany w Python)
- **Przetwarzanie obrazu:** Pillow (PIL), NumPy
- **Analiza / wykresy:** Matplotlib

---

## Struktura projektu

```
projekt_m2/
├── main.py                  # GUI + wszystkie algorytmy (główny plik)
├── analysis.py              # Automatyczna analiza + wykresy do dokumentacji
├── generate_test_images.py  # Generator obrazów testowych
├── requirements.txt         # Zależności Python
├── uruchom.bat              # Skrypt uruchomienia (Windows)
└── README.md
```

---

## Instalacja

### Wymagania

- Python 3.9+
- pip

### Kroki

```bash
# 1. Sklonuj repozytorium
git clone https://github.com/Wilkoz67/projekt_m2.git
cd projekt_m2

# 2. (Opcjonalnie) utwórz środowisko wirtualne
python -m venv venv
venv\Scripts\activate   # Windows
source venv/bin/activate  # Linux/macOS

# 3. Zainstaluj zależności
pip install -r requirements.txt
```

---

## Uruchomienie

### GUI (główna aplikacja)

```bash
python main.py
```

lub na Windows — dwuklik w `uruchom.bat`

### Generowanie wykresów analitycznych

```bash
python generate_test_images.py   # opcjonalnie — tworzy obrazy testowe
python analysis.py               # generuje wykresy i metryki w analysis_output/
```

---

## Algorytmy

### Etap 1 — Naiwny Scrambling

Każdy wiersz `i` przesuwany cyklicznie o `(i * key) % width`, każda kolumna `j` o `(j * key) % height`.  
**Słabość:** zachowuje lokalną strukturę pikseli — wzorce nadal widoczne.

### Etap 2 — Czysta Permutacja (Fisher-Yates)

Permutacja `P: {0..N-1} → {0..N-1}` generowana przez `np.random.default_rng(seed).shuffle`.  
Odwrotność: `P⁻¹[P[i]] = i` dla wszystkich `i`.  
**Weryfikacja:** `P⁻¹(P(i)) = i` — gwarantuje bezszkodowe odtworzenie.

### Etap 3 — Hybryda (Permutacja + XOR)

```
Scramble:    permutacja(piksel) → XOR z maską pseudolosową
Unscramble:  XOR z tą samą maską → odwrotna permutacja
```

XOR jest samoodwrotne: `f(f(x)) = x` — klucz wystarczy do odszyfrowania.

---

## Autor

**Marek Jancevic**  
[GitHub: Wilkoz67](https://github.com/Wilkoz67)

---

## Licencja

Projekt edukacyjny. Brak ograniczeń w użyciu akademickim.
