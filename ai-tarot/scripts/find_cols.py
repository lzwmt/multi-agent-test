#!/usr/bin/env python3
"""Find exact column boundaries by scanning brightness transitions."""
from PIL import Image
import numpy as np

img = Image.open('/root/.hermes/image_cache/img_c1f71f3c6565.png')
arr = np.array(img.convert('L'))

# Scan across the middle of row 0 (y=50-150)
row_slice = arr[50:150, :]
profile = row_slice.mean(axis=0)

# Find brightness transitions
diff = np.abs(np.diff(profile.astype(float)))
threshold = diff.mean() + 2 * diff.std()
raw_peaks = list(np.where(diff > threshold)[0])

# Cluster nearby peaks
clusters = []
group = [raw_peaks[0]]
for i in range(1, len(raw_peaks)):
    if raw_peaks[i] - raw_peaks[i-1] > 10:
        clusters.append(int(np.mean(group)))
        group = [raw_peaks[i]]
    else:
        group.append(raw_peaks[i])
clusters.append(int(np.mean(group)))

# Add edges
col_bounds = sorted(set([0] + clusters + [img.width]))

# Filter: keep boundaries that are >50px apart
filtered = [col_bounds[0]]
for b in col_bounds[1:]:
    if b - filtered[-1] > 50:
        filtered.append(b)
col_bounds = filtered

# We need exactly 11 boundaries for 10 cards
# If we have more, pick the 10 widest gaps
if len(col_bounds) > 11:
    gaps = [(col_bounds[i+1] - col_bounds[i], i) for i in range(len(col_bounds)-1)]
    gaps.sort(reverse=True)
    keep_indices = sorted([g[1] for g in gaps[:10]])
    col_bounds = [col_bounds[i] for i in keep_indices] + [col_bounds[keep_indices[-1]+1]]

widths = [col_bounds[i+1]-col_bounds[i] for i in range(len(col_bounds)-1)]
print(f"Boundaries: {col_bounds}")
print(f"Widths: {widths}")
print(f"Total: {sum(widths)}, Image: {img.width}")
