#!/usr/bin/env python3
"""Bước 1 của chuỗi v2: tạo lời đọc cho từng dòng trong script.json.

python3 tools/make_voice.py            -> audio/voice/lineNN.wav và audio/voice/voice.json
VOICE_ENGINE=say python3 tools/make_voice.py

Máy đọc chọn theo thứ tự, hoặc ép bằng VOICE_ENGINE=openai|gemini|gtts|say:
  openai  gpt-4o-mini-tts, có chỉ dẫn giọng, cần OPENAI_API_KEY (tốn phí, hỏi người dùng trước)
  gemini  Gemini TTS, cần GEMINI_API_KEY hoặc GOOGLE_API_KEY (tốn phí, hỏi người dùng trước)
  gtts    Google Translate TTS, không cần khoá, cần mạng. Tách câu theo dấu phẩy để có nhịp nghỉ
  say     macOS say giọng Linh, chạy máy hoàn toàn

Trường của mỗi dòng: sub là phụ đề, say là câu cho openai hoặc gemini,
tts là danh sách [ngôn ngữ, chữ] cho gtts và say, để tên tiếng Anh đọc bằng giọng tiếng Anh.
Bước này không xếp thời gian. Xếp dòng vào cảnh là việc của tools/layout.py.
"""
import hashlib, json, os, re, shutil, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mvlib import ff, duration, save_json  # noqa: E402

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V = os.path.join(HERE, "audio", "voice")
CACHE = os.path.join(V, "_cache")
os.makedirs(CACHE, exist_ok=True)
S = json.load(open(os.path.join(HERE, "script.json"), encoding="utf-8"))
STYLE = S.get("voiceStyle", "")

TRIM = ("silenceremove=start_periods=1:start_threshold=-42dB,areverse,"
        "silenceremove=start_periods=1:start_threshold=-42dB,areverse")
POLISH = ("highpass=f=90,equalizer=f=220:t=q:w=1:g=2,equalizer=f=3500:t=q:w=1.2:g=1.5,"
          "acompressor=threshold=-20dB:ratio=2.5:attack=8:release=120")


def pick_engine():
    e = os.environ.get("VOICE_ENGINE") or S.get("voiceEngine")
    if e:
        return e
    if os.environ.get("OPENAI_API_KEY"):
        return "openai"
    if os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"):
        return "gemini"
    try:
        import gtts  # noqa: F401
        return "gtts"
    except ImportError:
        return "say"


ENGINE = pick_engine()


def synth_openai(text, raw):
    from openai import OpenAI
    r = OpenAI().audio.speech.create(model="gpt-4o-mini-tts", voice=S.get("openaiVoice", "coral"), input=text,
                                     instructions=STYLE, response_format="wav")
    open(raw, "wb").write(r.content)


def synth_gemini(text, raw):
    import wave
    from google import genai
    from google.genai import types
    c = genai.Client(api_key=os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))
    r = c.models.generate_content(
        model=S.get("geminiModel", "gemini-2.5-flash-preview-tts"), contents=f"{STYLE}\n\n{text}",
        config=types.GenerateContentConfig(response_modalities=["AUDIO"], speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=S.get("geminiVoice", "Kore"))))))
    with wave.open(raw, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000)
        w.writeframes(r.candidates[0].content.parts[0].inline_data.data)


def _piece(lang, text, out):
    if ENGINE == "say":
        voice = S.get("sayVoices", {}).get(lang, {"vi": "Linh", "en": "Samantha"}.get(lang, "Linh"))
        aiff = out + ".aiff"
        import subprocess
        subprocess.run(["say", "-v", voice, "-r", str(S.get("sayRate", 175)), "-o", aiff, text], check=True)
        ff("-i", aiff, "-af", f"{TRIM},aresample=48000", "-ac", "1", out); os.remove(aiff)
    else:
        from gtts import gTTS
        mp3 = out + ".mp3"
        gTTS(text, lang=lang).save(mp3)
        ff("-i", mp3, "-af", f"{TRIM},aresample=48000", "-ac", "1", out); os.remove(mp3)


def synth_segments(segs, raw):
    """segs: [[lang, chữ], ...]. Tách tiếp theo dấu câu, chèn khoảng nghỉ theo loại dấu để có nhịp nói."""
    pieces = []
    for lang, txt in segs:
        for chunk in re.findall(r"[^,.!?;:]+[,.!?;:]*", txt):
            c = chunk.strip()
            if not c:
                continue
            wv = raw + f".{len(pieces)}.wav"
            _piece(lang, c, wv)
            end = c[-1]
            pieces.append((wv, 0.30 if end in ".!?" else 0.16 if end in ",;:" else 0.06))
    seq = []
    for k, (p, pause) in enumerate(pieces):
        seq.append(p)
        if k < len(pieces) - 1:
            pad = raw + f".pad{k}.wav"
            ff("-f", "lavfi", "-i", "anullsrc=r=48000:cl=mono", "-t", str(pause), pad)
            seq.append(pad)
    args = sum((["-i", p] for p in seq), [])
    ff(*args, "-filter_complex", "".join(f"[{k}:a]" for k in range(len(seq))) + f"concat=n={len(seq)}:v=0:a=1", raw)
    for p in seq:
        os.remove(p)


SPEED = S.get("voiceSpeed", {"openai": 1.0, "gemini": 1.04, "gtts": 1.13, "say": 1.0}[ENGINE])
print("máy đọc:", ENGINE, "tốc độ", SPEED)
meta = []
for i, ln in enumerate(S["lines"]):
    say = ln.get("say") or ln["sub"].replace("_", " ")
    segs = ln.get("tts") or [["vi", say]]
    spoken = say if ENGINE in ("openai", "gemini") else " ".join(t for _, t in segs)
    key = hashlib.sha1(json.dumps([ENGINE, STYLE, say, segs, S.get("openaiVoice"), S.get("geminiVoice"), S.get("sayVoices")],
                                  ensure_ascii=False).encode()).hexdigest()[:12]
    raw = os.path.join(CACHE, f"{ENGINE}_{key}.wav")
    if not os.path.exists(raw):
        if ENGINE == "openai":
            synth_openai(say, raw)
        elif ENGINE == "gemini":
            synth_gemini(say, raw)
        else:
            synth_segments(segs, raw)
    out = os.path.join(V, f"line{i:02d}.wav")
    ff("-i", raw, "-af", f"{TRIM},atempo={SPEED},{POLISH},aresample=48000", "-ac", "1", out)
    meta.append({"i": i, "file": f"audio/voice/line{i:02d}.wav", "dur": round(duration(out), 3), "spoken": spoken})
    print(f"  line{i:02d}  {meta[-1]['dur']:.2f}s  {ln['sub'].replace('_', ' ')}")
save_json({"engine": ENGINE, "speed": SPEED, "lines": meta}, os.path.join(V, "voice.json"))
if shutil.which("say") is None and ENGINE == "say":
    sys.exit("Máy không có lệnh say.")
