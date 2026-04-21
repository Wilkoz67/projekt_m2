"""
analysis.py
Automatyczna analiza wszystkich etapów - generuje raporty i wykresy.
Uruchom: python analysis.py
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")  # bez GUI
import matplotlib.pyplot as plt
from PIL import Image
import os
import math
import sys

# Import algorytmów z main
sys.path.insert(0, os.path.dirname(__file__))
from main import (
    NaiveScrambler, KeyedPermutationScrambler, HybridScrambler,
    compute_correlation, compute_pixel_difference, compute_psnr
)
from generate_test_images import checkerboard, gradient, synthetic_natural

OUTPUT_DIR = "analysis_output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

naive = NaiveScrambler()
permuter = KeyedPermutationScrambler()
hybrid = HybridScrambler()

CORRECT_KEY = 42
WRONG_KEY = 43


def load_or_generate_images():
    return {
        "Szachownica": checkerboard(256, 16),
        "Gradient": gradient(256),
        "Naturalny": synthetic_natural(256),
    }


def run_stage(stage_id, img_array, key):
    if stage_id == 1:
        scr = naive.scramble(img_array, key)
        rec = naive.unscramble(scr, key)
    elif stage_id == 2:
        scr = permuter.scramble(img_array, key)
        rec = permuter.unscramble(scr, key)
    else:
        scr = hybrid.scramble(img_array, key)
        rec = hybrid.unscramble(scr, key)
    return scr, rec


def compute_all_metrics(orig, scr, rec, wrong_rec):
    return {
        "corr_orig": compute_correlation(orig),
        "corr_scr": compute_correlation(scr),
        "diff_correct": compute_pixel_difference(orig, rec),
        "psnr_correct": compute_psnr(orig, rec),
        "diff_wrong": compute_pixel_difference(orig, wrong_rec),
        "psnr_wrong": compute_psnr(orig, wrong_rec),
    }


def plot_comparison(images_dict, stage_id, filename):
    """
    Dla każdego obrazu testowego rysuje: oryginał | scrambled | recovered.
    """
    n = len(images_dict)
    fig, axes = plt.subplots(n, 3, figsize=(12, 4 * n))
    fig.patch.set_facecolor("#0f0f1a")
    cols = ["Oryginał", "Przekształcony", "Odtworzony"]

    for row, (name, img) in enumerate(images_dict.items()):
        scr, rec = run_stage(stage_id, img, CORRECT_KEY)
        for col, (arr, title) in enumerate(zip([img, scr, rec], cols)):
            ax = axes[row, col] if n > 1 else axes[col]
            ax.imshow(arr)
            ax.set_title(f"{title}\n({name})", color="white", fontsize=9)
            ax.axis("off")
            ax.set_facecolor("#0f0f1a")

    for ax in (axes.flat if n > 1 else axes):
        ax.tick_params(colors="white")

    plt.suptitle(f"Etap {stage_id} – porównanie obrazów testowych",
                 color="#00ffcc", fontsize=13, fontweight="bold")
    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, filename)
    plt.savefig(path, dpi=120, bbox_inches="tight", facecolor="#0f0f1a")
    plt.close()
    print(f"Zapisano: {path}")


def plot_wrong_key(images_dict, stage_id, filename):
    """Porównanie: poprawny klucz vs błędny klucz."""
    n = len(images_dict)
    fig, axes = plt.subplots(n, 3, figsize=(12, 4 * n))
    fig.patch.set_facecolor("#0f0f1a")
    cols = ["Oryginał", f"Odtw. kl. {CORRECT_KEY}", f"Odtw. kl. {WRONG_KEY}"]

    for row, (name, img) in enumerate(images_dict.items()):
        scr, _ = run_stage(stage_id, img, CORRECT_KEY)
        _, rec_correct = run_stage(stage_id, img, CORRECT_KEY)
        if stage_id == 1:
            rec_wrong = naive.unscramble(scr, WRONG_KEY)
        elif stage_id == 2:
            rec_wrong = permuter.unscramble(scr, WRONG_KEY)
        else:
            rec_wrong = hybrid.unscramble(scr, WRONG_KEY)

        for col, (arr, title) in enumerate(zip([img, rec_correct, rec_wrong], cols)):
            ax = axes[row, col] if n > 1 else axes[col]
            ax.imshow(arr)
            ax.set_title(f"{title}\n({name})", color="white", fontsize=9)
            ax.axis("off")

    plt.suptitle(f"Etap {stage_id} – test błędnego klucza",
                 color="#ff6666", fontsize=13, fontweight="bold")
    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, filename)
    plt.savefig(path, dpi=120, bbox_inches="tight", facecolor="#0f0f1a")
    plt.close()
    print(f"Zapisano: {path}")


def plot_correlation_bars(images_dict):
    """Wykres słupkowy korelacji dla wszystkich etapów i obrazów."""
    img_names = list(images_dict.keys())
    stages = [1, 2, 3]
    stage_labels = ["Etap 1\n(Naiwny)", "Etap 2\n(Permutacja)", "Etap 3\n(Hybryda)"]
    colors_orig = ["#00cc88", "#0088ff", "#aa44ff"]
    colors_scr = ["#ff6666", "#ff9944", "#ffcc00"]

    x = np.arange(len(img_names))
    width = 0.12

    fig, ax = plt.subplots(figsize=(13, 6))
    fig.patch.set_facecolor("#0f0f1a")
    ax.set_facecolor("#0f0f1a")

    for si, (stage_id, slabel) in enumerate(zip(stages, stage_labels)):
        corr_orig_list = []
        corr_scr_list = []
        for name, img in images_dict.items():
            scr, _ = run_stage(stage_id, img, CORRECT_KEY)
            corr_orig_list.append(compute_correlation(img))
            corr_scr_list.append(compute_correlation(scr))

        offset = (si - 1) * width * 2.5
        bars1 = ax.bar(x + offset, corr_orig_list, width, label=f"{slabel} (oryg.)",
                       color=colors_orig[si], alpha=0.9)
        bars2 = ax.bar(x + offset + width, corr_scr_list, width, label=f"{slabel} (scr.)",
                       color=colors_scr[si], alpha=0.9)

    ax.set_xlabel("Obraz testowy", color="white")
    ax.set_ylabel("Korelacja sąsiednich pikseli", color="white")
    ax.set_title("Korelacja przed i po scrambligu – porównanie etapów",
                 color="#00ffcc", fontsize=12)
    ax.set_xticks(x)
    ax.set_xticklabels(img_names, color="white")
    ax.tick_params(colors="white")
    ax.axhline(0, color="white", linewidth=0.5, linestyle="--")
    ax.legend(loc="upper right", fontsize=8, facecolor="#1a1a35", labelcolor="white")
    ax.set_ylim(-0.2, 1.1)
    for spine in ax.spines.values():
        spine.set_edgecolor("#334466")

    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, "correlation_comparison.png")
    plt.savefig(path, dpi=120, bbox_inches="tight", facecolor="#0f0f1a")
    plt.close()
    print(f"Zapisano: {path}")


def print_metrics_table(images_dict):
    print("\n" + "="*80)
    print("TABELA METRYK – WSZYSTKIE ETAPY I OBRAZY")
    print("="*80)
    header = f"{'Obraz':<14} {'Etap':<8} {'Corr. oryg':>11} {'Corr. scr':>10} {'PSNR OK (dB)':>13} {'Diff OK':>9} {'Diff ZŁY':>9}"
    print(header)
    print("-"*80)

    for name, img in images_dict.items():
        for stage_id in [1, 2, 3]:
            scr, rec = run_stage(stage_id, img, CORRECT_KEY)
            if stage_id == 1:
                wrong_rec = naive.unscramble(scr, WRONG_KEY)
            elif stage_id == 2:
                wrong_rec = permuter.unscramble(scr, WRONG_KEY)
            else:
                wrong_rec = hybrid.unscramble(scr, WRONG_KEY)

            m = compute_all_metrics(img, scr, rec, wrong_rec)
            psnr_str = f"{m['psnr_correct']:.1f}" if m['psnr_correct'] != float('inf') else "∞"
            print(
                f"{name:<14} {stage_id:<8} "
                f"{m['corr_orig']:>11.4f} "
                f"{m['corr_scr']:>10.4f} "
                f"{psnr_str:>13} "
                f"{m['diff_correct']:>9.4f} "
                f"{m['diff_wrong']:>9.2f}"
            )
        print()

    print("="*80)


def verify_permutation_inverse():
    """Weryfikacja: P^-1(P(i)) = i."""
    print("\n=== WERYFIKACJA ODWROTNOŚCI PERMUTACJI (Etap 2) ===")
    for n in [100, 1000, 256*256]:
        ok = permuter.verify_inverse(n, CORRECT_KEY)
        print(f"  n={n:>7}, seed={CORRECT_KEY}: P^-1(P(i))=i dla wszystkich i: {'✓ OK' if ok else '✗ BŁĄD'}")


def avalanche_test(images_dict):
    """Test efektu lawinowego: 1-bitowa zmiana klucza -> zmiana w obrazie."""
    print("\n=== TEST EFEKTU LAWINOWEGO ===")
    img = list(images_dict.values())[0]
    for stage_id in [1, 2, 3]:
        scr_correct, _ = run_stage(stage_id, img, CORRECT_KEY)
        if stage_id == 1:
            scr_close = naive.scramble(img, CORRECT_KEY + 1)
        elif stage_id == 2:
            scr_close = permuter.scramble(img, CORRECT_KEY + 1)
        else:
            scr_close = hybrid.scramble(img, CORRECT_KEY + 1)

        diff = compute_pixel_difference(scr_correct, scr_close)
        changed_pixels = np.sum(np.any(scr_correct != scr_close, axis=2))
        total_pixels = img.shape[0] * img.shape[1]
        pct = 100 * changed_pixels / total_pixels
        print(f"  Etap {stage_id}: klucz {CORRECT_KEY} vs {CORRECT_KEY+1} | "
              f"śr. diff={diff:.2f} | zmienione piksele: {changed_pixels}/{total_pixels} ({pct:.1f}%)")


if __name__ == "__main__":
    print("Generowanie obrazów testowych...")
    images = load_or_generate_images()

    print("\nGenerowanie wykresów porównawczych...")
    for sid in [1, 2, 3]:
        plot_comparison(images, sid, f"stage{sid}_comparison.png")
        plot_wrong_key(images, sid, f"stage{sid}_wrong_key.png")

    plot_correlation_bars(images)

    print_metrics_table(images)
    verify_permutation_inverse()
    avalanche_test(images)

    print(f"\n✓ Wszystkie wyniki w folderze: {OUTPUT_DIR}/")
