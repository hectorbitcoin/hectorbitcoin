#!/usr/bin/env python3
"""Ensambla los animatics MP4 de nusava (keyframe + Ken Burns + VO por escena).

Uso: python3 nusava/build_animatic.py
Requiere: imageio-ffmpeg (pip install --user --break-system-packages imageio-ffmpeg)
"""
import os, re, subprocess, sys

import imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)))

VIDEOS = {
    "video1": {
        "windows": [3, 5, 5, 5, 4, 3],
        "scenes": ["scene1_hook", "scene2_problem", "scene3_product",
                   "scene4_demo", "scene5_energy", "scene6_cta"],
        "audio": ["video1_scene%d.mp3" % i for i in range(1, 7)],
    },
    "video2": {
        "windows": [3, 4, 4, 4, 3],
        "scenes": ["scene1_hook", "scene2_problem", "scene3_solution",
                   "scene4_result", "scene5_cta"],
        "audio": ["video2_scene%d.mp3" % i for i in range(1, 6)],
    },
}


def probe_dur(path):
    out = subprocess.run([FF, "-i", path], capture_output=True, text=True)
    m = re.search(r"Duration:\s+(\d+):(\d+):(\d+\.\d+)", out.stderr)
    if not m:
        return 0.0
    h, mi, s = m.groups()
    return int(h) * 3600 + int(mi) * 60 + float(s)


def build_scene(video, idx, scene, audio, window, tmp):
    img = os.path.join(ROOT, video, scene + ".png")
    aud = os.path.join(ROOT, "audio", audio)
    adur = probe_dur(aud)
    dur = max(window, adur + 0.4)
    frames = int(round(dur * 30))
    out = os.path.join(tmp, "%s_s%d.mp4" % (video, idx))
    if idx % 2 == 0:  # zoom in
        z = "min(1+0.12*on/%d,1.12)" % frames
    else:             # zoom out
        z = "max(1.12-0.12*on/%d,1.0)" % frames
    fc = ("[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
          "crop=1080:1920,setsar=1,fps=30,"
          "zoompan=z='%s':d=1:s=1080x1920,format=yuv420p[v];"
          "[1:a]apad=whole_dur=%.2f[a]" % (z, dur))
    cmd = [FF, "-y", "-loop", "1", "-t", "%.2f" % dur, "-i", img, "-i", aud,
           "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
           "-c:a", "aac", "-b:a", "128k", "-t", "%.2f" % dur, out]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr[-2000:], file=sys.stderr)
        raise SystemExit("ffmpeg fallo en %s escena %d" % (video, idx))
    print("  %s escena %d: %.1fs (audio %.1fs)" % (video, idx, dur, adur))
    return out, dur


def main():
    import tempfile
    for video, cfg in VIDEOS.items():
        with tempfile.TemporaryDirectory() as tmp:
            parts, total = [], 0.0
            for i, (scene, audio, win) in enumerate(
                    zip(cfg["scenes"], cfg["audio"], cfg["windows"]), 1):
                out, dur = build_scene(video, i, scene, audio, win, tmp)
                parts.append(out)
                total += dur
            listf = os.path.join(tmp, "list.txt")
            with open(listf, "w") as f:
                for p in parts:
                    f.write("file '%s'\n" % p)
            final = os.path.join(ROOT, video + "_animatic.mp4")
            r = subprocess.run([FF, "-y", "-f", "concat", "-safe", "0",
                                "-i", listf, "-c", "copy", final],
                               capture_output=True, text=True)
            if r.returncode != 0:
                print(r.stderr[-2000:], file=sys.stderr)
                raise SystemExit("concat fallo en " + video)
            print("%s -> %s (%.1fs total)" % (video, final, total))


if __name__ == "__main__":
    main()
