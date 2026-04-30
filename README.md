# Image Scrambler

> Reversible image encryption using permutation, XOR substitution, and chaos-based algorithms — with a Tkinter GUI.

![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![NumPy](https://img.shields.io/badge/NumPy-1.24%2B-013243?style=flat-square&logo=numpy&logoColor=white)
![Pillow](https://img.shields.io/badge/Pillow-10.0%2B-yellow?style=flat-square)
![Matplotlib](https://img.shields.io/badge/Matplotlib-3.7%2B-orange?style=flat-square)
![Tkinter](https://img.shields.io/badge/GUI-Tkinter-lightgrey?style=flat-square)

---

## About the Project

This project demonstrates three progressive stages of digital image scrambling (encryption), each increasing in security and complexity:

| Stage | Method | Key |
|-------|--------|-----|
| **1 – Naive Scrambling** | Cyclic row/column shifts (`np.roll`) | Integer shift value |
| **2 – Pure Permutation** | Fisher-Yates shuffle with inverse permutation P⁻¹ | Random seed |
| **3 – Hybrid** | Permutation + XOR substitution with pseudorandom mask | Random seed |

Every stage implements both `scramble` and `unscramble` — the original image can be **fully recovered** from the scrambled version using the same key.

---

## Tech Stack

- **Language:** Python 3.9+
- **GUI:** Tkinter (built-in)
- **Image processing:** Pillow (PIL), NumPy
- **Analysis & charts:** Matplotlib

---

## Project Structure

```
projekt_m2/
├── main.py                   # GUI + all scrambling algorithms
├── analysis.py               # Automated analysis & chart generation
├── generate_test_images.py   # Test image generator
├── requirements.txt          # Python dependencies
├── uruchom.bat               # Windows launcher script
└── README.md
```

---

## Installation

**Requirements:** Python 3.9+, pip

```bash
# 1. Clone the repository
git clone https://github.com/Wilkoz67/projekt_m2.git
cd projekt_m2

# 2. (Optional) create a virtual environment
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # Linux / macOS

# 3. Install dependencies
pip install -r requirements.txt
```

---

## Usage

### GUI (main application)

```bash
python main.py
```

Or on Windows — double-click `uruchom.bat`

### Generate analytical charts

```bash
python generate_test_images.py   # optional — creates test images
python analysis.py               # generates charts and metrics in analysis_output/
```

---

## Algorithms

### Stage 1 — Naive Scrambling

Each row `i` is cyclically shifted by `(i * key) % width`, each column `j` by `(j * key) % height`.  
**Weakness:** preserves local pixel structure — patterns remain partially visible.

### Stage 2 — Pure Permutation (Fisher-Yates)

Permutation `P: {0..N-1} → {0..N-1}` generated via `np.random.default_rng(seed).shuffle`.  
Inverse: `P⁻¹[P[i]] = i` for all `i`.  
**Verification:** `P⁻¹(P(i)) = i` — guarantees lossless recovery.

### Stage 3 — Hybrid (Permutation + XOR)

```
Scramble:    permute(pixel) → XOR with pseudorandom mask
Unscramble:  XOR with same mask → inverse permutation
```

XOR is self-inverse: `f(f(x)) = x` — the key alone is sufficient to decrypt.

---

## Author

**Marek Jancevic** · [GitHub: Wilkoz67](https://github.com/Wilkoz67)

---

## License

Educational project. No restrictions for academic use.
