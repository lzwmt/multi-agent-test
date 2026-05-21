#!/bin/bash
# 生成播客片头片尾 BGM - 改进版
# 使用多层音效叠加 + 混响 + 节奏，生成更专业的氛围音

BGMDIR="/root/.openclaw/workspace/ai-podcast/bgm"
mkdir -p "$BGMDIR"

# === 片头 BGM (5秒) ===
# 多层叠加：低音铺底 + 中音和弦 + 高音点缀 + 轻微节奏
ffmpeg -y \
  -f lavfi -i "sine=frequency=130.81:duration=5" \
  -f lavfi -i "sine=frequency=261.63:duration=5" \
  -f lavfi -i "sine=frequency=329.63:duration=5" \
  -f lavfi -i "sine=frequency=392.00:duration=5" \
  -f lavfi -i "sine=frequency=523.25:duration=5" \
  -f lavfi -i "sine=frequency=783.99:duration=5" \
  -filter_complex "
    [0]volume=0.08[bass];
    [1]volume=0.12[c4];
    [2]volume=0.10[e4];
    [3]volume=0.10[g4];
    [4]volume=0.06[c5];
    [5]volume=0.04[g5];
    [bass][c4]amix=inputs=2[bc];
    [bc][e4]amix=inputs=2[bce];
    [bce][g4]amix=inputs=2[bceg];
    [bceg][c5]amix=inputs=2[bcegc];
    [bcegc][g5]amix=inputs=2[all];
    [all]afade=t=in:st=0:d=1.5,
          afade=t=out:st=3.5:d=1.5,
          aecho=0.8:0.88:60:0.4,
          equalizer=f=300:width_type=h:width=200:g=3,
          equalizer=f=2000:width_type=h:width=1000:g=-2,
          volume=1.5[out]
  " \
  -map "[out]" \
  -ar 24000 -ac 1 \
  "$BGMDIR/intro.mp3" 2>/dev/null

echo "✅ 片头 BGM: $BGMDIR/intro.mp3"

# === 片尾 BGM (8秒) ===
# 温暖收尾感：Am调 + 渐弱
ffmpeg -y \
  -f lavfi -i "sine=frequency=110.00:duration=8" \
  -f lavfi -i "sine=frequency=220.00:duration=8" \
  -f lavfi -i "sine=frequency=261.63:duration=8" \
  -f lavfi -i "sine=frequency=329.63:duration=8" \
  -f lavfi -i "sine=frequency=440.00:duration=8" \
  -filter_complex "
    [0]volume=0.06[bass];
    [1]volume=0.10[a3];
    [2]volume=0.10[c4];
    [3]volume=0.08[e4];
    [4]volume=0.05[a4];
    [bass][a3]amix=inputs=2[ba];
    [ba][c4]amix=inputs=2[bac];
    [bac][e4]amix=inputs=2[bace];
    [bace][a4]amix=inputs=2[all];
    [all]afade=t=in:st=0:d=1.0,
          afade=t=out:st=4.0:d=4.0,
          aecho=0.8:0.9:80:0.5,
          equalizer=f=250:width_type=h:width=200:g=2,
          volume=1.2[out]
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
