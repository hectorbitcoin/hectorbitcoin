#!/usr/bin/env python3
"""Ensambla los videos finales de nusava (keyframe + Ken Burns + VO + textos).

Uso: python3 nusava/build_animatic.py
Sale: nusava/video1_final.mp4 y nusava/video2_final.mp4
(1080x1920, h264+aac, titulos/captions/disclaimer quemados via libass, VO sync)
Requiere: imageio-ffmpeg (pip install --user --break-system-packages imageio-ffmpeg)
"""
import os, re, subprocess, sys, tempfile

import imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)))
DISCLAIMER = "Suplemento dietario. No diagnostica,\\Ntrata ni previene enfermedades."

VIDEOS = {
    "video1": {
        "title": "CÓMO DEJÉ EL CAFÉ",
        "brand": "nusava · B12 que sí se siente",
        "windows": [3, 5, 5, 5, 4, 3],
        "scenes": ["scene1_hook", "scene2_problem", "scene3_product",
                   "scene4_demo", "scene5_energy", "scene6_cta"],
        "audio": ["video1_scene%d.mp3" % i for i in range(1, 7)],
        "caps": [
            "Yo también vivía\\Npegado del café.",
            "Cuatro tazas al día, y a las tres\\Nde la tarde ya estaba dormido.",
            "Hasta que probé nusava:\\NB12 en gotas, debajo\\Nde la lengua, y listo.",
            "Sin bajones, sin nervios,\\Ny sin el cuarto café de la tarde.",
            "Energía pareja para entrenar\\Ny para todo el día.",
            "Nusava.\\NB12 que sí se siente.",
        ],
    },
    "video2": {
        "title": "DEJÉ LAS PASTILLAS",
        "brand": "nusava · B12 que sí se siente",
        "windows": [3, 4, 4, 4, 3],
        "scenes": ["scene1_hook", "scene2_problem", "scene3_solution",
                   "scene4_result", "scene5_cta"],
        "audio": ["video2_scene%d.mp3" % i for i in range(1, 6)],
        "caps": [
            "Yo también creía que todas\\Nlas B12 eran iguales.",
            "Me tomaba la pastilla con agua,\\Ny no sentía nada.",
            "Cambié a las goticas\\Nsublinguales de nusava.",
            "Energía, foco y ánimo\\Ndesde la primera semana.",
            "Nusava.\\NYo a las pastillas no vuelvo.",
        ],
    },
}

ASS_HEAD = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,DejaVu Sans,52,&H00FFFFFF,&H000000FF,&H00000000,&H99000000,-1,0,0,0,100,100,0,0,3,0,0,2,40,40,210,1
Style: Title,DejaVu Sans,76,&H00FFFFFF,&H000000FF,&H00000000,&H99000000,-1,0,0,0,100,100,0,0,3,0,0,8,40,40,150,1
Style: Brand,DejaVu Sans,46,&H00FFFFFF,&H000000FF,&H00000000,&H99000000,-1,0,0,0,100,100,0,0,3,0,0,8,40,40,420,1
Style: Small,DejaVu Sans,30,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,3,0,0,2,40,40,60,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def ts(s):
    return "0:%02d:%05.2f" % (int(s // 60), s % 60)


def probe_dur(path):
    out = subprocess.run([FF, "-i", path], capture_output=True, text=True)
    m = re.search(r"Duration:\s+(\d+):(\d+):(\d+\.\d+)", out.stderr)
    if not m:
        return 0.0
    h, mi, s = m.groups()
    return int(h) * 3600 + int(mi) * 60 + float(s)


def write_ass(cfg, idx, n, dur, tmp):
    lines = [ASS_HEAD]
    lines.append("Dialogue: 0,%s,%s,Cap,,0,0,0,,%s"
                 % (ts(0), ts(dur), cfg["caps"][idx - 1]))
    if idx == 1:
        lines.append("Dialogue: 0,%s,%s,Title,,0,0,0,,%s"
                     % (ts(0), ts(dur), cfg["title"]))
    if idx == n:
        lines.append("Dialogue: 0,%s,%s,Brand,,0,0,0,,%s"
                     % (ts(0), ts(dur), cfg["brand"]))
        lines.append("Dialogue: 0,%s,%s,Small,,0,0,0,,%s"
                     % (ts(0), ts(dur), DISCLAIMER))
    p = os.path.join(tmp, "sub%d.ass" % idx)
    with open(p, "w") as f:
        f.write("\n".join(lines) + "\n")
    return p


def build_scene(video, cfg, idx, n, scene, audio, window, tmp):
    img = os.path.join(ROOT, video, scene + ".png")
    aud = os.path.join(ROOT, "audio", audio)
    adur = probe_dur(aud)
    dur = max(window, adur + 0.4)
    frames = int(round(dur * 30))
    out = os.path.join(tmp, "%s_s%d.mp4" % (video, idx))
    z = ("min(1+0.12*on/%d,1.12)" % frames) if idx % 2 == 0 \
        else ("max(1.12-0.12*on/%d,1.0)" % frames)
    assf = write_ass(cfg, idx, n, dur, tmp)
    fc = ("[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
          "crop=1080:1920,setsar=1,fps=30,"
          "zoompan=z='%s':d=1:s=1080x1920,"
          "ass=%s,format=yuv420p[v];"
          "[1:a]apad=whole_dur=%.2f[a]" % (z, assf, dur))
    cmd = [FF, "-y", "-loop", "1", "-t", "%.2f" % dur, "-i", img, "-i", aud,
           "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
           "-c:a", "aac", "-b:a", "128k", "-t", "%.2f" % dur, out]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr[-3000:], file=sys.stderr)
        raise SystemExit("ffmpeg fallo en %s escena %d" % (video, idx))
    print("  %s escena %d: %.1fs" % (video, idx, dur))
    return out, dur


def assemble(parts, final, T=0.4):
    durs = [probe_dur(p) for p in parts]
    n = len(parts)
    inputs = []
    for p in parts:
        inputs += ["-i", p]
    fc, prev, cum = [], "[0:v]", durs[0]
    for i in range(1, n):
        out = "[x%d]" % i
        fc.append("%s[%d:v]xfade=transition=fade:duration=%.2f:offset=%.2f%s"
                  % (prev, i, T, cum - T, out))
        prev = out
        cum += durs[i] - T
    preva = "[0:a]"
    for i in range(1, n):
        outa = "[a%d]" % i
        fc.append("%s[%d:a]acrossfade=d=%.2f%s" % (preva, i, T, outa))
        preva = outa
    cmd = [FF, "-y"] + inputs + ["-filter_complex", ";".join(fc),
           "-map", prev, "-map", preva,
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
           "-c:a", "aac", "-b:a", "128k", final]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr[-3000:], file=sys.stderr)
        raise SystemExit("xfade fallo en " + final)
    return cum


def main():
    for video, cfg in VIDEOS.items():
        n = len(cfg["scenes"])
        with tempfile.TemporaryDirectory() as tmp:
            parts, total = [], 0.0
            for i, (scene, audio, win) in enumerate(
                    zip(cfg["scenes"], cfg["audio"], cfg["windows"]), 1):
                out, dur = build_scene(video, cfg, i, n, scene, audio, win,
                                       tmp)
                parts.append(out)
                total += dur
            final = os.path.join(ROOT, video + "_final.mp4")
            total = assemble(parts, final)
            print("%s -> %s (%.1fs con crossfades)" % (video, final, total))


if __name__ == "__main__":
    main()
