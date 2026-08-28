#!/usr/bin/env python3
"""Genera pistas de VO completas y .srt alineados al timeline final (con crossfades).

Sale:
  nusava/audio/video1_vo_full.mp3 , video2_vo_full.mp3  (una sola pista con silencios)
  nusava/subs/video1.srt , video2.srt                   (captions listos p/CapCut)

Los starts replican la cadena xfade/acrossfade de build_animatic.py (T=0.4 s).
"""
import os, re, subprocess

import imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)))
T = 0.4

VIDEOS = {
    "video1": {
        "windows": [3, 5, 5, 5, 4, 3],
        "audio": ["video1_scene%d.mp3" % i for i in range(1, 7)],
        "caps": [
            "Yo también vivía pegado del café.",
            "Cuatro tazas al día, y a las tres de la tarde ya estaba dormido.",
            "Hasta que probé nusava: B12 en gotas, debajo de la lengua, y listo.",
            "Sin bajones, sin nervios, y sin el cuarto café de la tarde.",
            "Energía pareja para entrenar y para todo el día.",
            "Nusava. B12 que sí se siente.",
        ],
    },
    "video2": {
        "windows": [3, 4, 4, 4, 3],
        "audio": ["video2_scene%d.mp3" % i for i in range(1, 6)],
        "caps": [
            "Yo también creía que todas las B12 eran iguales.",
            "Me tomaba la pastilla con agua, y no sentía nada.",
            "Cambié a las goticas sublinguales de nusava.",
            "Energía, foco y ánimo desde la primera semana.",
            "Nusava. Yo a las pastillas no vuelvo.",
        ],
    },
}


def probe_dur(path):
    out = subprocess.run([FF, "-i", path], capture_output=True, text=True)
    m = re.search(r"Duration:\s+(\d+):(\d+):(\d+\.\d+)", out.stderr)
    h, mi, s = m.groups()
    return int(h) * 3600 + int(mi) * 60 + float(s)


def srt_ts(t):
    h = int(t // 3600)
    m = int(t % 3600 // 60)
    s = t % 60
    return "%02d:%02d:%06.3f" % (h, m, s)


def main():
    os.makedirs(os.path.join(ROOT, "subs"), exist_ok=True)
    for video, cfg in VIDEOS.items():
        adurs = [probe_dur(os.path.join(ROOT, "audio", a))
                 for a in cfg["audio"]]
        durs = [max(w, a + 0.4) for w, a in zip(cfg["windows"], adurs)]
        starts, acc = [], 0.0
        for i, d in enumerate(durs):
            starts.append(acc)
            acc += d - T
        total = acc

        # pista completa: cada mp3 con adelay a su start, amix sin normalizar
        inputs, flt = [], []
        for i, a in enumerate(cfg["audio"]):
            inputs += ["-i", os.path.join(ROOT, "audio", a)]
            ms = int(round(starts[i] * 1000))
            flt.append("[%d:a]adelay=%d|%d,apad=whole_dur=%.2f[d%d]"
                       % (i, ms, ms, total, i))
        mix = "".join("[d%d]" % i for i in range(len(cfg["audio"])))
        flt.append("%samix=inputs=%d:normalize=0,atrim=0:%.2f[a]"
                   % (mix, len(cfg["audio"]), total))
        out = os.path.join(ROOT, "audio", video + "_vo_full.mp3")
        r = subprocess.run([FF, "-y"] + inputs + ["-filter_complex",
                           ";".join(flt), "-map", "[a]", "-c:a", "libmp3lame",
                           "-q:a", "4", out], capture_output=True, text=True)
        if r.returncode != 0:
            raise SystemExit(r.stderr[-2000:])
        print("%s -> %s (%.1fs)" % (video, out, total))

        # srt
        lines = []
        for i, cap in enumerate(cfg["caps"]):
            t0 = starts[i] + 0.15
            t1 = min(starts[i] + durs[i] - 0.1, starts[i] + adurs[i] + 0.3)
            lines.append("%d\n%s --> %s\n%s\n" % (
                i + 1, srt_ts(t0).replace(".", ","),
                srt_ts(t1).replace(".", ","), cap))
        sp = os.path.join(ROOT, "subs", video + ".srt")
        with open(sp, "w") as f:
            f.write("\n".join(lines))
        print("%s -> %s" % (video, sp))


if __name__ == "__main__":
    main()
