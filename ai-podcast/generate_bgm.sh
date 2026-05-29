#!/bin/bash
# 生成播客片头片尾 BGM
# 使用 ffmpeg 的多层正弦波叠加 + 混响，生成柔和的电子氛围音

BGMDIR="/root/.openclaw/workspace/ai-podcast/bgm"
mkdir -p "$BGMDIR"

# === 片头 BGM (4秒) ===
# C大调和弦: C4(261.63) + E4(329.63) + G4(392.00)，柔和渐入渐出
ffmpeg -y \
  -f lavfi -i "sine=frequency=261.63:duration=4" \
  -f lavfi -i "sine=frequency=329.63:duration=4" \
  -f lavfi -i "sine=frequency=392.00:duration=4" \
  -f lavfi -i "sine=frequency=523.25:duration=4" \
  -filter_complex "
    [0]volume=0.15[a];
    [1]volume=0.12[b];
    [2]volume=0.10[c];
    [3]volume=0.08[d];
    [a][b]amix=inputs=2[ab];
    [ab][c]amix=inputs=2[abc];
    [abc][d]amix=inputs=2[all];
    [all]afade=t=in:st=0:d=1.5,
          afade=t=out:st=2.5:d=1.5,
          aecho=0.8:0.88:60:0.4,
          equalizer=f=300:width_type=h:width=200:g=3,
          volume=1.2[out]
  " \
  -map "[out]" \
  -ar 24000 -ac 1 \
  "$BGMDIR/intro.mp3" 2>/dev/null

echo "✅ 片头 BGM: $BGMDIR/intro.mp3"

# === 片尾 BGM (6秒) ===
# Am调: A3(220) + C4(261.63) + E4(329.63)，温暖收尾感
ffmpeg -y \
  -f lavfi -i "sine=frequency=220.00:duration=6" \
  -f lavfi -i "sine=frequency=261.63:duration=6" \
  -f lavfi -i "sine=frequency=329.63:duration=6" \
  -f lavfi -i "sine=frequency=440.00:duration=6" \
  -filter_complex "
    [0]volume=0.12[a];
    [1]volume=0.10[b];
    [2]volume=0.10[c];
    [3]volume=0.06[d];
    [a][b]amix=inputs=2[ab];
    [ab][c]amix=inputs=2[abc];
    [abc][d]amix=inputs=2[all];
    [all]afade=t=in:st=0:d=1.0,
          afade=t=out:st=3.5:d=2.5,
          aecho=0.8:0.9:80:0.5,
          equalizer=f=250:width_type=h:width=200:g=2,
          volume=1.0[out]
  " \
  -map "[out]" \
  -ar 24000 -ac 1 \
  "$BGMDIR/outro.mp3" 2>/dev/null

echo "✅ 片尾 BGM: $BGMDIR/outro.mp3"

# 验证
for f in "$BGMDIR/intro.mp3" "$BGMDIR/outro.mp3"; do
  dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$f" 2>/dev/null)
  size=$(du -h "$f" | cut -f1)
  echo "  $(basename $f): ${dur}s, ${size}"
done
