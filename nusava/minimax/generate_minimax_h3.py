#!/usr/bin/env python3
"""Genera los 11 clips de nusava con MiniMax-H3 (fal.ai, image-to-video).

Uso:
  export FAL_KEY=...                        # tu clave de fal.ai
  python3 nusava/minimax/generate_minimax_h3.py            # genera y descarga
  python3 nusava/minimax/generate_minimax_h3.py --dry-run  # solo payloads

Cada escena usa su keyframe 9:16 público (GitHub raw) como first_frame
(image_url): el aspect ratio de salida hereda el 9:16 de la imagen.
H3 dura 5-15 s por clip (mínimo 5: las escenas de 3-4 s se generan a 5 s
y se recortan en el edit). resolution por defecto 768P (~$0.30/clip);
cámbiala con RES=2K (≈$0.65/clip) o RES=480P (≈$0.25/clip).
prompt_expansion_mode=disabled para que no reinterprete la etiqueta nusava.
"""
import json, os, sys, time, urllib.request

ENDPOINT = "minimax/h3/image-to-video"
QUEUE = "https://queue.fal.run/" + ENDPOINT
RAW = ("https://raw.githubusercontent.com/hectorbitcoin/hectorbitcoin/"
       "arena/01a04a94-hectorbitcoin/nusava/")
OUT = os.path.dirname(os.path.abspath(__file__))
RES = os.environ.get("RES", "768P")

SCENES = [
    ("video1_scene1", "video1/scene1_hook.png", 3,
     "Close-up of a fit young man in his late 20s looking directly at camera with a tired expression, gym background blurred, natural afternoon lighting, cinematic shallow depth of field, camera slowly pushes in on his face, vertical 9:16"),
    ("video1_scene2", "video1/scene2_problem.png", 5,
     "Medium shot of a tired person sitting at a desk yawning, three empty coffee cups on the desk, afternoon golden light through a window, head resting on hand, laptop open but ignored, documentary style, natural colors, vertical 9:16"),
    ("video1_scene3", "video1/scene3_product.png", 5,
     "Close-up of hands holding a 60ml dark amber glass dropper bottle with black cap and white label showing green leaf logo nusava, green VEGAN badge, red bar B12 5000mcg, yellow bar B6 3400mcg, orange bar B1 2400mcg, NIACIN+FOLATE, RASPBERRY FLAVOR, bottle identical to the first frame. Person examines the bottle in kitchen lighting, shallow depth of field, casual authentic feel, camera slowly rotates around the bottle, vertical 9:16"),
    ("video1_scene4", "video1/scene4_demo.png", 5,
     "Close-up of a person tilting head back, eyes closed, placing sublingual drops under their tongue from a glass dropper holding deep red raspberry liquid, natural morning light, kitchen background, slow deliberate action, authentic handheld camera feel, vertical 9:16"),
    ("video1_scene5", "video1/scene5_energy.png", 4,
     "Dynamic shot of a fit person training energetically in a gym, lifting weights with focus and power, sweat visible, warm gym lighting, cinematic motion blur, motivational energy, vertical 9:16"),
    ("video1_scene6", "video1/scene6_cta.png", 3,
     "Product hero shot of the nusava 60ml dark amber dropper bottle standing next to its black retail box with red benefits panel, centered on clean white surface, soft natural window light, minimalist aesthetic, slight bokeh, professional but authentic, vertical 9:16"),
    ("video2_scene1", "video2/scene1_hook.png", 3,
     "Medium shot of a young woman in her mid-20s holding a white supplement pill bottle, looking at camera with skeptical knowing expression, slight head shake, casual home setting, natural daylight, authentic UGC feel, vertical 9:16"),
    ("video2_scene2", "video2/scene2_problem.png", 4,
     "Close-up of a hand dropping a white pill into a clear glass of water, pill sinks slowly with small bubbles forming, camera follows the pill down, macro shot, clean kitchen setting, soft lighting, vertical 9:16"),
    ("video2_scene3", "video2/scene3_solution.png", 4,
     "Hands opening a 60ml dark amber nusava bottle, pulling out the glass dropper showing deep red raspberry liquid, camera focuses on the drop forming at the tip, warm natural lighting, kitchen background blurred, product reveal moment, vertical 9:16"),
    ("video2_scene4", "video2/scene4_result.png", 4,
     "Quick montage of a person training in gym with energy, then focused working on laptop, then walking outside with sunlight on face, warm golden tones, person looks vibrant and healthy, dynamic cuts, lifestyle feel, vertical 9:16"),
    ("video2_scene5", "video2/scene5_cta.png", 3,
     "The same young woman now smiling confidently, holding the nusava 60ml amber dropper bottle next to her face, warm natural light, product visible and in focus, authentic testimonial style, vertical 9:16"),
]


def req(url, key, data=None):
    r = urllib.request.Request(
        url, data=json.dumps(data).encode() if data is not None else None,
        headers={"Authorization": "Key " + key,
                 "Content-Type": "application/json"},
        method="POST" if data is not None else "GET")
    with urllib.request.urlopen(r) as resp:
        return json.load(resp)


def main():
    dry = "--dry-run" in sys.argv
    key = os.environ.get("FAL_KEY", "")
    if not dry and not key:
        sys.exit("Falta FAL_KEY. Exporta tu clave de fal.ai o usa --dry-run "
                 "para ver los payloads.")
    for name, img, win, prompt in SCENES:
        payload = {
            "prompt": prompt,
            "image_url": RAW + img,
            "duration": max(5, win),          # H3: minimo 5 s
            "resolution": RES,
            "prompt_expansion_mode": "disabled",
        }
        if dry:
            print(json.dumps(payload, indent=2))
            continue
        sub = req(QUEUE, key, payload)
        rid, status_url, response_url = (sub["request_id"], sub["status_url"],
                                         sub["response_url"])
        print(name, "-> request", rid)
        while True:
            st = req(status_url, key).get("status")
            if st == "COMPLETED":
                break
            if st in ("FAILED", "ERROR"):
                raise SystemExit("fallo %s: %s" % (rid, st))
            time.sleep(8)
        url = req(response_url, key)["video"]["url"]
        dest = os.path.join(OUT, name + ".mp4")
        urllib.request.urlretrieve(url, dest)
        print("  descargado:", dest)


if __name__ == "__main__":
    main()
