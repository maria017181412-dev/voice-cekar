"""
এই স্ক্রিপ্টটা শুধু একটা fixed test sentence দিয়ে F5-TTS চালায় এবং
বাস্তব সময় মাপে — কোনো assumption না, শুধু real number।

Output: output/benchmark/timing_result.json + benchmark.wav
"""

import json
import time
from pathlib import Path

REF_AUDIO = Path("voices/narrator/reference.wav")
REF_TEXT_FILE = Path("voices/narrator/reference.txt")
OUT_DIR = Path("output/benchmark")

# প্রায় ২৫-৩০ শব্দের একটা fixed বাক্য — বাস্তব chunk-এর কাছাকাছি সাইজ
TEST_TEXT = (
    "This is a fixed benchmark sentence used to measure how long F5-TTS "
    "takes to generate speech on this machine, so we know real numbers "
    "instead of guesses."
)


def main():
    if not REF_AUDIO.exists():
        raise SystemExit(
            f"[FAIL] Reference audio পাওয়া যায়নি: {REF_AUDIO}\n"
            "voices/narrator/reference.wav যোগ করো (৫-১৫ সেকেন্ড clean single-speaker audio)।"
        )
    if not REF_TEXT_FILE.exists():
        raise SystemExit(
            f"[FAIL] Reference transcript পাওয়া যায়নি: {REF_TEXT_FILE}\n"
            "voices/narrator/reference.txt-এ reference.wav-এ ঠিক যা বলা হয়েছে তার exact transcript লেখো।"
        )

    ref_text = REF_TEXT_FILE.read_text(encoding="utf-8").strip()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # ভারী import গুলো এখানে করা হচ্ছে যাতে উপরের check গুলো দ্রুত fail করতে পারে
    import soundfile as sf
    from f5_tts.api import F5TTS

    print("[1/3] Model লোড হচ্ছে (F5TTS_v1_Base)... এতে কিছুটা সময় লাগবে, এটাও মাপা হচ্ছে।")
    load_start = time.time()
    f5tts = F5TTS(model="F5TTS_v1_Base")
    load_elapsed = time.time() - load_start
    print(f"    model load সময়: {load_elapsed:.2f}s")

    print("[2/3] Generation চলছে...")
    gen_start = time.time()
    wav, sr, _spec = f5tts.infer(
        ref_file=str(REF_AUDIO),
        ref_text=ref_text,
        gen_text=TEST_TEXT,
        seed=0,
    )
    gen_elapsed = time.time() - gen_start

    audio_path = OUT_DIR / "benchmark.wav"
    sf.write(str(audio_path), wav, sr)
    duration = len(wav) / sr

    rtf = gen_elapsed / duration if duration > 0 else None

    result = {
        "model_load_seconds": round(load_elapsed, 2),
        "generation_seconds": round(gen_elapsed, 2),
        "generated_audio_seconds": round(duration, 2),
        "real_time_factor_RTF": round(rtf, 3) if rtf else None,
        "test_text_word_count": len(TEST_TEXT.split()),
        "note": (
            "RTF = generation_seconds / generated_audio_seconds. "
            "RTF=1 মানে real-time গতি। RTF=10 মানে ১ সেকেন্ড audio বানাতে ১০ সেকেন্ড সময় লাগে। "
            "model_load_seconds আলাদা রাখা হয়েছে কারণ এটা শুধু একবার (per shard job) লাগবে, প্রতি chunk-এ না — "
            "যদি অনেক chunk একই shard job-এ loop করে generate করা হয়, তাহলে এই load সময়টা amortize হয়ে যাবে।"
        ),
    }

    print("\n[3/3] ফলাফল:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    (OUT_DIR / "timing_result.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
