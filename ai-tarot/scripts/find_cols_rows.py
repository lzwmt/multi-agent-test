#!/usr/bin/env python3
"""Detect column boundaries for specific rows."""
from PIL import Image
import numpy as np

img = Image.open('/root/.hermes/image_cache/img_c1f71f3c6565.png')
arr = np.array(img.convert('L'))

ROW_Y = [9, 219, 409, 588, 741, 905, 1058, 1240, 1418]

def find_col_bounds(y1, y2, label):
    mid = (y1 + y2) // 2
    half = min(40, (y2 - y1) // 4)
    row_slice = arr[mid-half:mid+half, :]
    profile = row_slice.mean(axis=0)
    diff = np.abs(np.diff(profile.astype(float)))
    threshold = diff.mean() + 2 * diff.std()
    raw_peaks = list(np.where(diff > threshold)[0])
    if not raw_peaks:
        print(f"{label}: no peaks found!")
        return []
    clusters = []
    group = [raw_peaks[0]]
    for i in range(1, len(raw_peaks)):
        if raw_peaks[i] - raw_peaks[i-1] > 10:
            clusters.append(int(np.mean(group)))
            group = [raw_peaks[i]]
        else:
            group.append(raw_peaks[i])
    clusters.append(int(np.mean(group)))
    col_bounds = sorted(set([0] + clusters + [img.width]))
    filtered = [col_bounds[0]]
    for b in col_bounds[1:]:
        if b - filtered[-1] > 50:
            filtered.append(b)
    widths = [filtered[i+1]-filtered[i] for i in range(len(filtered)-1)]
    print(f"{label}: bounds={filtered}, widths={widths}")
    return filtered

for row in [3, 4, 7]:
    find_col_bounds(ROW_Y[row], ROW_Y[row+1], f"Row{row}")
