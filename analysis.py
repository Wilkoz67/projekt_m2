"""
analysis.py
Automatyczna analiza wszystkich etapów - generuje raporty i wykresy.
Uruchom: python analysis.py
"""

import sys
import io

# Zapewnia poprawne wyświetlanie polskich znaków w konsoli Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.patches import FancyBboxPatch
import matplotlib.patheffects as pe
from PIL import Image
import os
import math

sys.path.insert(0, os.path.dirname(__file__))
from main import (
    NaiveScrambler, KeyedPermutationScrambler, HybridScrambler,
    compute_correlation, compute_pixel_difference, compute_psnr
)
from generate_test_images import checkerboard, gradient, synthetic_natural

OUTPUT_DIR = "analysis_output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

naive    = NaiveScrambler()
permuter = KeyedPermutationScrambler()
hybrid   = HybridScrambler()

CORRECT_KEY = 42
WRONG_KEY   = 43

# ============================================================
# PALETA / STYL
# ============================================================

C = {
    "bg":       "#080812",
    "bg_panel": "#0e0e22",
    "border":   "#1e1e3c",
    "accent":   "#00e5b0",
    "accent2":  "#7b5ea7",
    "text":     "#c8d0e8",
    "dim":      "#4a5070",
    "red":      "#ff5555",
    "orange":   "#ff9944",
    "blue":     "#44aaff",
    "green":    "#44dd88",
    "yellow":   "#ffdd44",
}

STAGE_COLORS = {
    1: ("#44aaff", "#1a2a4a"),
    2: ("#aa66ff", "#2a1a4a"),
    3: ("#44dd88", "#1a3a2a"),
}

PANEL_COLS = ["#00e5b0", "#ff8833", "#4499ff"]


def apply_global_style():
    """Ustawia globalne rcParams dla spójnego stylu ciemnego."""
    plt.rcParams.update({
        "figure.facecolor":     C["bg"],
        "axes.facecolor":       C["bg_panel"],
        "axes.edgecolor":       C["border"],
        "axes.labelcolor":      C["text"],
        "axes.titlecolor":      C["text"],
        "xtick.color":          C["dim"],
        "ytick.color":          C["dim"],
        "text.color":           C["text"],
        "grid.color":           C["border"],
        "grid.linewidth":       0.6,
        "grid.alpha":           0.6,
        "legend.facecolor":     C["bg_panel"],
        "legend.edgecolor":     C["border"],
        "legend.labelcolor":    C["text"],
        "font.family":          "monospace",
        "figure.dpi":           100,
    })


apply_global_style()


# ============================================================
# HELPERS
# ============================================================

def fig_title(fig, text, subtitle=""):
    """Stylizowany tytuł figury z opcjonalnym podtytułem."""
    fig.text(
        0.5, 0.98, text,
        ha="center", va="top",
        fontsize=14, fontweight="bold",
        color=C["accent"],
        fontfamily="monospace",
    )
    if subtitle:
        fig.text(
            0.5, 0.955, subtitle,
            ha="center", va="top",
            fontsize=9, color=C["dim"],
            fontfamily="monospace",
        )


def styled_img_ax(ax, arr, title, subtitle="", border_color="#00e5b0"):
    """Wyświetla obraz na osi z estetycznym tytułem i ramką."""
    ax.imshow(arr, interpolation="nearest")
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_edgecolor(border_color)
        spine.set_linewidth(2)

    # Tytuł na kolorowym tle
    ax.set_title(title, fontsize=9, fontweight="bold",
                 color="#000000",
                 fontfamily="monospace",
                 pad=3,
                 bbox=dict(boxstyle="square,pad=0.3",
                           fc=border_color, ec="none"))
    if subtitle:
        ax.annotate(
            subtitle,
            xy=(0.5, -0.04), xycoords="axes fraction",
            ha="center", va="top",
            fontsize=7.5, color=C["dim"],
            fontfamily="monospace",
        )


def metric_badge(ax, text, color=None, pos="bottom"):
    """Naklejka z metryką pod/nad obrazem."""
    color = color or C["accent"]
    y = -0.13 if pos == "bottom" else 1.08
    ax.annotate(
        text,
        xy=(0.5, y), xycoords="axes fraction",
        ha="center", va="top",
        fontsize=7.5, color=color,
        fontfamily="monospace",
        bbox=dict(boxstyle="round,pad=0.3",
                  fc=C["bg"], ec=color, lw=0.8, alpha=0.9),
    )


def load_or_generate_images():
    return {
        "Szachownica": checkerboard(256, 16),
        "Gradient":    gradient(256),
        "Naturalny":   synthetic_natural(256),
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
        "corr_orig":    compute_correlation(orig),
        "corr_scr":     compute_correlation(scr),
        "diff_correct": compute_pixel_difference(orig, rec),
        "psnr_correct": compute_psnr(orig, rec),
        "diff_wrong":   compute_pixel_difference(orig, wrong_rec),
        "psnr_wrong":   compute_psnr(orig, wrong_rec),
    }


# ============================================================
# WYKRESY
# ============================================================

def plot_comparison(images_dict, stage_id, filename):
    """
    Oryginał | Przekształcony | Odtworzony — dla każdego obrazu testowego.
    Dodaje metryki korelacji i PSNR na każdym panelu.
    """
    n = len(images_dict)
    stage_col, stage_bg = STAGE_COLORS[stage_id]
    stage_names = {1: "Naiwny scrambling", 2: "Czysta permutacja", 3: "Hybryda (P + XOR)"}

    fig = plt.figure(figsize=(14, 4.8 * n + 1.2))
    fig.patch.set_facecolor(C["bg"])

    fig_title(
        fig,
        f"ETAP {stage_id}  ·  {stage_names[stage_id]}  ·  Porównanie obrazów testowych",
        subtitle=f"klucz = {CORRECT_KEY}"
    )

    # Pionowa linia dekoracyjna
    fig.add_artist(plt.Line2D(
        [0.01, 0.01], [0.02, 0.96],
        transform=fig.transFigure,
        color=stage_col, linewidth=3, alpha=0.7
    ))

    outer = gridspec.GridSpec(
        n, 1,
        figure=fig,
        top=0.93, bottom=0.05,
        hspace=0.55,
        left=0.04, right=0.97
    )

    col_titles  = ["ORYGINAŁ",        "PRZEKSZTAŁCONY",    "ODTWORZONY"]
    col_colors  = [PANEL_COLS[0],      PANEL_COLS[1],        PANEL_COLS[2]]

    for row, (name, img) in enumerate(images_dict.items()):
        scr, rec = run_stage(stage_id, img, CORRECT_KEY)

        c_orig = compute_correlation(img)
        c_scr  = compute_correlation(scr)
        psnr   = compute_psnr(img, rec)
        diff   = compute_pixel_difference(img, rec)
        psnr_s = f"{psnr:.1f} dB" if psnr != float('inf') else "∞ dB"

        inner = gridspec.GridSpecFromSubplotSpec(
            1, 3,
            subplot_spec=outer[row],
            wspace=0.06
        )

        arrays  = [img,   scr,  rec]
        metrics = [
            f"corr = {c_orig:+.3f}",
            f"corr = {c_scr:+.3f}",
            f"PSNR = {psnr_s}  ·  diff = {diff:.2f}",
        ]
        m_colors = [
            C["accent"],
            C["green"]  if abs(c_scr) < 0.1 else C["orange"],
            C["green"]  if psnr > 60 or psnr == float('inf') else C["yellow"],
        ]

        for col in range(3):
            ax = fig.add_subplot(inner[col])
            styled_img_ax(
                ax, arrays[col],
                f"{col_titles[col]}  ({name})",
                border_color=col_colors[col]
            )
            metric_badge(ax, metrics[col], color=m_colors[col])

    plt.savefig(
        os.path.join(OUTPUT_DIR, filename),
        dpi=130, bbox_inches="tight",
        facecolor=C["bg"]
    )
    plt.close()
    print(f"  Zapisano: {filename}")


def plot_wrong_key(images_dict, stage_id, filename):
    """Porównanie odtworzenia poprawnym vs błędnym kluczem + mapa różnic."""
    n = len(images_dict)
    stage_col, _  = STAGE_COLORS[stage_id]
    stage_names   = {1: "Naiwny scrambling", 2: "Czysta permutacja", 3: "Hybryda (P + XOR)"}

    fig = plt.figure(figsize=(16, 4.8 * n + 1.2))
    fig.patch.set_facecolor(C["bg"])

    fig_title(
        fig,
        f"ETAP {stage_id}  ·  {stage_names[stage_id]}  ·  Test błędnego klucza",
        subtitle=f"klucz poprawny = {CORRECT_KEY}   |   klucz błędny = {WRONG_KEY}"
    )
    fig.add_artist(plt.Line2D(
        [0.01, 0.01], [0.02, 0.96],
        transform=fig.transFigure,
        color=C["red"], linewidth=3, alpha=0.7
    ))

    outer = gridspec.GridSpec(
        n, 1,
        figure=fig,
        top=0.93, bottom=0.05,
        hspace=0.55, left=0.04, right=0.97
    )

    for row, (name, img) in enumerate(images_dict.items()):
        scr, rec_correct = run_stage(stage_id, img, CORRECT_KEY)
        if stage_id == 1:
            rec_wrong = naive.unscramble(scr, WRONG_KEY)
        elif stage_id == 2:
            rec_wrong = permuter.unscramble(scr, WRONG_KEY)
        else:
            rec_wrong = hybrid.unscramble(scr, WRONG_KEY)

        diff_img    = np.abs(img.astype(int) - rec_wrong.astype(int)).astype(np.uint8)
        diff_mean   = compute_pixel_difference(img, rec_wrong)
        psnr_ok     = compute_psnr(img, rec_correct)
        psnr_ok_s   = f"{psnr_ok:.1f} dB" if psnr_ok != float('inf') else "∞ dB"

        inner = gridspec.GridSpecFromSubplotSpec(
            1, 4,
            subplot_spec=outer[row],
            wspace=0.06,
            width_ratios=[1, 1, 1, 1]
        )

        # Oryginał
        ax0 = fig.add_subplot(inner[0])
        styled_img_ax(ax0, img, f"ORYGINAŁ  ({name})", border_color=PANEL_COLS[0])
        metric_badge(ax0, f"corr = {compute_correlation(img):+.3f}", color=C["accent"])

        # Odtworzony poprawnym kluczem
        ax1 = fig.add_subplot(inner[1])
        styled_img_ax(ax1, rec_correct, f"KLUCZ {CORRECT_KEY}  (OK)", border_color=C["green"])
        metric_badge(ax1, f"PSNR = {psnr_ok_s}", color=C["green"])

        # Odtworzony błędnym kluczem
        ax2 = fig.add_subplot(inner[2])
        styled_img_ax(ax2, rec_wrong, f"KLUCZ {WRONG_KEY}  (BŁĘDNY)", border_color=C["red"])
        metric_badge(ax2, f"diff = {diff_mean:.1f}", color=C["red"])

        # Mapa różnic
        ax3 = fig.add_subplot(inner[3])
        ax3.imshow(diff_img, cmap="hot", interpolation="nearest")
        ax3.set_xticks([])
        ax3.set_yticks([])
        for spine in ax3.spines.values():
            spine.set_edgecolor(C["orange"])
            spine.set_linewidth(2)
        ax3.set_title("MAPA RÓŻNIC", fontsize=9, fontweight="bold",
                      color="#000000", fontfamily="monospace", pad=3,
                      bbox=dict(boxstyle="square,pad=0.3", fc=C["orange"], ec="none"))
        metric_badge(ax3, f"śr. różnica = {diff_mean:.1f}", color=C["orange"])

    plt.savefig(
        os.path.join(OUTPUT_DIR, filename),
        dpi=130, bbox_inches="tight",
        facecolor=C["bg"]
    )
    plt.close()
    print(f"  Zapisano: {filename}")


def plot_correlation_bars(images_dict):
    """
    Wykres słupkowy korelacji przed/po scrambligu dla wszystkich etapów.
    Dodaje etykiety wartości na słupkach.
    """
    img_names    = list(images_dict.keys())
    stages       = [1, 2, 3]
    stage_labels = ["Etap 1\nNaiwny", "Etap 2\nPermutacja", "Etap 3\nHybryda"]
    orig_cols    = [C["blue"],   C["accent2"], C["green"]]
    scr_cols     = [C["orange"], C["red"],     C["yellow"]]

    x     = np.arange(len(img_names))
    width = 0.11

    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    fig.patch.set_facecolor(C["bg"])

    fig_title(
        fig,
        "ANALIZA KORELACJI  ·  Porównanie wszystkich etapów",
        subtitle="Korelacja sąsiednich pikseli przed i po scrambligu"
    )

    # --- Lewy wykres: słupkowy ---
    ax = axes[0]
    ax.set_facecolor(C["bg_panel"])
    for spine in ax.spines.values():
        spine.set_edgecolor(C["border"])

    all_bars = []
    all_labels = []

    for si, (stage_id, slabel) in enumerate(zip(stages, stage_labels)):
        corr_orig_list = []
        corr_scr_list  = []
        for name, img in images_dict.items():
            scr, _ = run_stage(stage_id, img, CORRECT_KEY)
            corr_orig_list.append(compute_correlation(img))
            corr_scr_list.append(compute_correlation(scr))

        offset = (si - 1) * width * 2.4
        b1 = ax.bar(
            x + offset, corr_orig_list, width,
            color=orig_cols[si], alpha=0.88,
            label=f"{slabel} – oryginał",
            zorder=3
        )
        b2 = ax.bar(
            x + offset + width, corr_scr_list, width,
            color=scr_cols[si], alpha=0.88,
            label=f"{slabel} – po scr.",
            zorder=3
        )
        all_bars.extend([b1, b2])
        all_labels.extend([f"{slabel} – oryg.", f"{slabel} – scr."])

        # Etykiety wartości na słupkach
        for bar, val in zip(b1, corr_orig_list):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.015,
                f"{val:.2f}",
                ha="center", va="bottom",
                fontsize=6.5, color=orig_cols[si],
                fontfamily="monospace"
            )
        for bar, val in zip(b2, corr_scr_list):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.015 if val >= 0 else bar.get_height() - 0.04,
                f"{val:.2f}",
                ha="center", va="bottom",
                fontsize=6.5, color=scr_cols[si],
                fontfamily="monospace"
            )

    ax.axhline(0, color=C["dim"], linewidth=0.8, linestyle="--", zorder=2)
    ax.axhline(0.1, color=C["green"], linewidth=0.5,
               linestyle=":", alpha=0.5, zorder=2)
    ax.annotate("prog dobrego scrambligu",
                xy=(x[-1] + 0.4, 0.1), fontsize=6.5,
                color=C["green"], alpha=0.7, fontfamily="monospace")

    ax.set_xlabel("Obraz testowy", labelpad=8, fontsize=10)
    ax.set_ylabel("Korelacja sąsiednich pikseli", labelpad=8, fontsize=10)
    ax.set_title("Korelacja przed / po scrambligu",
                 fontsize=11, fontweight="bold", color=C["accent"], pad=10)
    ax.set_xticks(x)
    ax.set_xticklabels(img_names, fontsize=10)
    ax.set_ylim(-0.25, 1.15)
    ax.yaxis.grid(True, zorder=0)
    ax.legend(
        fontsize=7.5, loc="upper right",
        framealpha=0.9, ncol=2,
        handlelength=1.4
    )

    # --- Prawy wykres: redukcja korelacji (delta) ---
    ax2 = axes[1]
    ax2.set_facecolor(C["bg_panel"])
    for spine in ax2.spines.values():
        spine.set_edgecolor(C["border"])

    bar_w = 0.22
    for si, (stage_id, slabel, col) in enumerate(
            zip(stages, stage_labels, [C["blue"], C["accent2"], C["green"]])):
        deltas = []
        for name, img in images_dict.items():
            scr, _ = run_stage(stage_id, img, CORRECT_KEY)
            deltas.append(abs(compute_correlation(img) - compute_correlation(scr)))

        offset = (si - 1) * bar_w * 1.15
        b = ax2.bar(
            x + offset, deltas, bar_w,
            color=col, alpha=0.85, label=slabel, zorder=3
        )
        for bar, val in zip(b, deltas):
            ax2.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.008,
                f"{val:.3f}",
                ha="center", va="bottom",
                fontsize=7, color=col,
                fontfamily="monospace"
            )

    ax2.set_xlabel("Obraz testowy", labelpad=8, fontsize=10)
    ax2.set_ylabel("Redukcja korelacji  |Δcorr|", labelpad=8, fontsize=10)
    ax2.set_title("Efektywność scrambligu  —  |Δkorelacja|",
                  fontsize=11, fontweight="bold", color=C["accent"], pad=10)
    ax2.set_xticks(x)
    ax2.set_xticklabels(img_names, fontsize=10)
    ax2.set_ylim(0, 1.15)
    ax2.yaxis.grid(True, zorder=0)
    ax2.legend(fontsize=8, loc="upper right", framealpha=0.9)

    plt.tight_layout(rect=[0, 0, 1, 0.93])
    path = os.path.join(OUTPUT_DIR, "correlation_chart.png")
    plt.savefig(path, dpi=130, bbox_inches="tight", facecolor=C["bg"])
    plt.close()
    print(f"  Zapisano: correlation_chart.png")


def plot_stage_full(images_dict, stage_id, filename):
    """
    Zbiorczy raport etapu: oryginał + scrambled + odtworzony + histogramy jasności.
    """
    n = len(images_dict)
    stage_col, _  = STAGE_COLORS[stage_id]
    stage_names   = {1: "Naiwny scrambling", 2: "Czysta permutacja", 3: "Hybryda (P + XOR)"}

    cols_per_row = 4   # oryg | scr | rec | histogram

    fig = plt.figure(figsize=(16, 4.6 * n + 1.4))
    fig.patch.set_facecolor(C["bg"])

    fig_title(
        fig,
        f"ETAP {stage_id}  ·  {stage_names[stage_id]}  ·  Pełny raport",
        subtitle=f"klucz = {CORRECT_KEY}   |   obrazy testowe: {', '.join(images_dict.keys())}"
    )
    fig.add_artist(plt.Line2D(
        [0.01, 0.01], [0.02, 0.96],
        transform=fig.transFigure,
        color=stage_col, linewidth=3, alpha=0.7
    ))

    outer = gridspec.GridSpec(
        n, 1,
        figure=fig,
        top=0.93, bottom=0.04,
        hspace=0.6, left=0.04, right=0.97
    )

    for row, (name, img) in enumerate(images_dict.items()):
        scr, rec = run_stage(stage_id, img, CORRECT_KEY)

        c_orig = compute_correlation(img)
        c_scr  = compute_correlation(scr)
        psnr   = compute_psnr(img, rec)
        diff   = compute_pixel_difference(img, rec)
        psnr_s = f"{psnr:.1f} dB" if psnr != float('inf') else "∞ dB"

        inner = gridspec.GridSpecFromSubplotSpec(
            1, cols_per_row,
            subplot_spec=outer[row],
            wspace=0.08,
            width_ratios=[1, 1, 1, 1.2]
        )

        # Oryginał
        ax0 = fig.add_subplot(inner[0])
        styled_img_ax(ax0, img, f"ORYGINAŁ  ({name})", border_color=PANEL_COLS[0])
        metric_badge(ax0, f"corr = {c_orig:+.3f}", color=C["accent"])

        # Przekształcony
        ax1 = fig.add_subplot(inner[1])
        styled_img_ax(ax1, scr, "PRZEKSZTAŁCONY", border_color=PANEL_COLS[1])
        scr_color = C["green"] if abs(c_scr) < 0.1 else C["orange"]
        metric_badge(ax1, f"corr = {c_scr:+.3f}", color=scr_color)

        # Odtworzony
        ax2 = fig.add_subplot(inner[2])
        styled_img_ax(ax2, rec, "ODTWORZONY", border_color=PANEL_COLS[2])
        metric_badge(ax2, f"PSNR = {psnr_s}", color=C["green"] if psnr > 60 or psnr == float('inf') else C["yellow"])

        # Histogram jasności (porównanie oryginał vs scrambled)
        ax3 = fig.add_subplot(inner[3])
        ax3.set_facecolor(C["bg_panel"])
        for spine in ax3.spines.values():
            spine.set_edgecolor(C["border"])

        gray_orig = np.mean(img, axis=2).flatten()
        gray_scr  = np.mean(scr, axis=2).flatten()

        bins = np.linspace(0, 255, 48)
        ax3.hist(gray_orig, bins=bins, color=PANEL_COLS[0], alpha=0.55,
                 label="Oryginał", density=True)
        ax3.hist(gray_scr, bins=bins, color=PANEL_COLS[1], alpha=0.55,
                 label="Scrambled", density=True)
        ax3.set_xlim(0, 255)
        ax3.set_xlabel("Jasność", fontsize=7.5, labelpad=4)
        ax3.set_ylabel("Gęstość", fontsize=7.5, labelpad=4)
        ax3.set_title("Histogram jasności", fontsize=8, fontweight="bold",
                      color=C["text"], pad=4)
        ax3.tick_params(labelsize=7)
        ax3.yaxis.grid(True, alpha=0.4)
        ax3.legend(fontsize=7, loc="upper center", framealpha=0.8)

    plt.savefig(
        os.path.join(OUTPUT_DIR, filename),
        dpi=130, bbox_inches="tight",
        facecolor=C["bg"]
    )
    plt.close()
    print(f"  Zapisano: {filename}")


# ============================================================
# TABELA METRYK + TESTY KONSOLOWE
# ============================================================

def print_metrics_table(images_dict):
    print("\n" + "=" * 80)
    print("TABELA METRYK – WSZYSTKIE ETAPY I OBRAZY")
    print("=" * 80)
    header = (f"{'Obraz':<14} {'Etap':<8} {'Corr. oryg':>11} "
              f"{'Corr. scr':>10} {'PSNR OK (dB)':>13} {'Diff OK':>9} {'Diff ZŁY':>9}")
    print(header)
    print("-" * 80)
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
                f"{m['corr_orig']:>11.4f} {m['corr_scr']:>10.4f} "
                f"{psnr_str:>13} {m['diff_correct']:>9.4f} {m['diff_wrong']:>9.2f}"
            )
        print()
    print("=" * 80)


def verify_permutation_inverse():
    print("\n=== WERYFIKACJA ODWROTNOŚCI PERMUTACJI (Etap 2) ===")
    for n in [100, 1000, 256 * 256]:
        ok = permuter.verify_inverse(n, CORRECT_KEY)
        print(f"  n={n:>7}, seed={CORRECT_KEY}: P^-1(P(i))=i: {'✓ OK' if ok else '✗ BŁĄD'}")


def avalanche_test(images_dict):
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
        changed = np.sum(np.any(scr_correct != scr_close, axis=2))
        total   = img.shape[0] * img.shape[1]
        pct     = 100 * changed / total
        print(f"  Etap {stage_id}: klucz {CORRECT_KEY} vs {CORRECT_KEY+1} | "
              f"śr. diff={diff:.2f} | zmienione: {changed}/{total} ({pct:.1f}%)")


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print("Generowanie obrazów testowych...")
    images = load_or_generate_images()

    print("\nGenerowanie wykresów...")
    for sid in [1, 2, 3]:
        print(f"\n  --- Etap {sid} ---")
        plot_comparison(images, sid, f"stage{sid}_comparison.png")
        plot_wrong_key(images, sid, f"stage{sid}_wrong_key.png")
        plot_stage_full(images, sid, f"stage{sid}_full.png")

    print("\n  --- Korelacja (wykres zbiorczy) ---")
    plot_correlation_bars(images)

    print_metrics_table(images)
    verify_permutation_inverse()
    avalanche_test(images)

    print(f"\n✓ Wszystkie wyniki w folderze: {OUTPUT_DIR}/")
