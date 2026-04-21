"""
generate_test_images.py
Generuje obrazy testowe do eksperymentów:
  - szachownica (silna struktura)
  - gradient (struktura ciągła)
  - naturalny (symulowany)
"""

import numpy as np
from PIL import Image
import os

OUTPUT_DIR = "test_images"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def checkerboard(size=256, tile=16) -> np.ndarray:
    """Szachownica - silna periodyczna struktura."""
    img = np.zeros((size, size, 3), dtype=np.uint8)
    for i in range(size):
        for j in range(size):
            if ((i // tile) + (j // tile)) % 2 == 0:
                img[i, j] = [255, 255, 255]
            else:
                img[i, j] = [0, 0, 0]
    return img


def gradient(size=256) -> np.ndarray:
    """Gradient poziomy i pionowy - wysoka korelacja sąsiednich pikseli."""
    img = np.zeros((size, size, 3), dtype=np.uint8)
    for i in range(size):
        for j in range(size):
            r = int(255 * i / size)
            g = int(255 * j / size)
            b = int(255 * (i + j) / (2 * size))
            img[i, j] = [r, g, b]
    return img


def synthetic_natural(size=256) -> np.ndarray:
    """Syntetyczny obraz 'naturalny' - mozaika kolorowych bloków + szum."""
    rng = np.random.default_rng(7)
    img = np.zeros((size, size, 3), dtype=np.uint8)
    colors = [
        [70, 130, 180], [34, 139, 34], [210, 105, 30],
        [220, 20, 60], [100, 149, 237], [255, 215, 0]
    ]
    block = size // 4
    for bi in range(4):
        for bj in range(4):
            c = colors[(bi * 4 + bj) % len(colors)]
            for ci in range(3):
                img[bi*block:(bi+1)*block, bj*block:(bj+1)*block, ci] = (
                    np.clip(rng.integers(c[ci]-30, c[ci]+30, (block, block)), 0, 255)
                )
    return img


if __name__ == "__main__":
    images = {
        "checkerboard.png": checkerboard(),
        "gradient.png": gradient(),
        "synthetic_natural.png": synthetic_natural(),
    }

    for name, arr in images.items():
        path = os.path.join(OUTPUT_DIR, name)
        Image.fromarray(arr).save(path)
        print(f"Zapisano: {path}")

    print("Gotowe!")
