#!/usr/bin/env python3
"""Genera los 11 clips de nusava con Wan 3.0 (Alibaba Model Studio / DashScope).

Uso:
  export DASHSCOPE_API_KEY=sk-...          # tu clave de Alibaba Cloud Model Studio
  python3 nusava/wan3/generate_wan3.py     # genera y descarga los MP4 aquí

  python3 nusava/wan3/generate_wan3.py --dry-run   # solo imprime los payloads

Cada escena usa su keyframe 9:16 (ya público en GitHub raw) como first_frame,
ratio 9:16, resolución 720P y la duración del storyboard. Jobs asíncronos:
1-5 min por clip según Alibaba.
"""
import json, os, sys, time, urllib.request

BASE = "https://dashscope-intl.aliyuncs.com/api/v1"
RAW = ("https://raw.githubusercontent.com/hectorbitcoin/hectorbitcoin/"
       "arena/01a04a94-hectorbitcoin/nusava/")
OUT = os.path.dirname(os.path.abspath(__file__))

SCENES = [
    # (nombre, keyframe, duración, prompt)
    ("video1_scene1", "video1/scene1_hook.png", 3,
     "Close-up of a fit young man in his late 20s looking directly at camera with a tired expression, gym background blurred, natural afternoon lighting, cinematic shallow depth of field, camera slowly pushes in on his face, vertical 9:16"),
    ("video1_scene2", "video1/scene2_problem.png", 5,
     "Medium shot of a tired person sitting at a desk yawning, three empty coffee cups on the desk, afternoon golden light through a window, head resting on hand, laptop open but ignored, documentary style, natural colors, vertical 9:16"),
    ("video1_scene3", "video1/scene3_product.png", 5,
     "Close-up of hands holding a 60ml dark amber glass dropper bottle with black cap and white label showing green leaf logo nusava, green VEGAN badge, red bar B12 5000mcg, yellow bar B6 3400mcg, orange bar B1 2400mcg, NIACIN+FOLATE, RASPBERRY FLAVOR, bottle matches the first frame exactly. Person examines the bottle in kitchen lighting, shallow depth of field, casual authentic feel, camera slowly rotates around the bottle, vertical 9:16"),
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


def post(payload, key):
    req = urllib.request.Request(
        BASE + "/services/aigc/video-generation/video-synthesis",
        data=json.dumps(payload).encode(),
        headers={"Authorization": "Bearer " + key,
                 "Content-Type": "application/json",
                 "X-DashScope-Async": "enable"})
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def poll(task_id, key, timeout=900):
    req = urllib.request.Request(BASE + "/tasks/" + task_id,
                                 headers={"Authorization": "Bearer " + key})
    t0 = time.time()
    while time.time() - t0 < timeout:
        with urllib.request.urlopen(req) as r:
            data = json.load(r)
        st = data.get("output", {}).get("task_status")
        if st == "SUCCEEDED":
            return data["output"]
        if st in ("FAILED", "CANCELED"):
            raise SystemExit("task %s: %s" % (task_id, json.dumps(data)))
        time.sleep(10)
    raise SystemExit("timeout esperando task " + task_id)


def main():
    dry = "--dry-run" in sys.argv
    key = os.environ.get("DASHSCOPE_API_KEY", "")
    if not dry and not key:
        sys.exit("Falta DASHSCOPE_API_KEY. Exporta tu clave de Alibaba Cloud "
                 "Model Studio o usa --dry-run para ver los payloads.")
    for name, img, dur, prompt in SCENES:
        payload = {
            "model": "wan3.0-video",
            "input": {
                "prompt": prompt,
                "media": [{"type": "first_frame", "url": RAW + img}],
            },
            "parameters": {"resolution": "720P", "ratio": "9:16",
                           "duration": dur},
        }
        if dry:
            print(json.dumps(payload, indent=2))
            continue
        task_id = post(payload, key)["output"]["task_id"]
        print(name, "-> task", task_id)
        out = poll(task_id, key)
        url = out.get("video_url") or out.get("results", [{}])[0].get("url")
        dest = os.path.join(OUT, name + ".mp4")
        urllib.request.urlretrieve(url, dest)
        print("  descargado:", dest)


if __name__ == "__main__":
    main()
