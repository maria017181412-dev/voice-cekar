"""
Phone থেকে যেভাবেই record করা হোক না কেন (m4a, mp3, aac, 3gp, ogg — যা-ই হোক),
এই script সেটাকে খুঁজে বের করে F5-TTS-এর জন্য উপযুক্ত একটা clean reference.wav-এ
convert করে দেয়। ম্যানুয়ালি কোনো converter app/website লাগবে না।

শুধু voices/narrator/ ফোল্ডারে তোমার phone-এর raw recording রাখো
(যেমন reference.m4a বা reference.mp3), নাম "reference" রাখলেই হবে,
extension যা-ই হোক — এই script বাকিটা সামলাবে।
"""

import subprocess
import sys
from pathlib import Path

VOICE_DIR = Path("voices/narrator")
FINAL_WAV = VOICE_DIR / "reference.wav"

# এই extension-গুলোর মধ্যে যেকোনো একটা raw recording হিসেবে ধরা হবে
CANDIDATE_EXTS = [".m4a", ".mp3", ".aac", ".3gp", ".3gpp", ".ogg", ".opus", ".wma", ".caf", ".wav"]


def find_raw_recording():
    for ext in CANDIDATE_EXTS:
        candidates = list(VOICE_DIR.glob(f"reference{ext}")) + list(VOICE_DIR.glob(f"reference{ext.upper()}"))
        for c in candidates:
            yield c


def main():
    if not VOICE_DIR.exists():
        raise SystemExit(f"[FAIL] {VOICE_DIR} ফোল্ডার পাওয়া যায়নি।")

    found = list(find_raw_recording())
    if not found:
        raise SystemExit(
            f"[FAIL] {VOICE_DIR} ফোল্ডারে কোনো reference.* audio file পাওয়া যায়নি।\n"
            "phone-এ যেভাবেই record করেছো (m4a/mp3/যেকোনো ফরম্যাট), ফাইলটার নাম "
            "'reference' রেখে এই ফোল্ডারে রাখো (যেমন reference.m4a)।"
        )

    # যদি একাধিক candidate পাওয়া যায়, প্রথমটা নেওয়া হবে; বাকিগুলো সম্পর্কে জানানো হবে
    source = found[0]
    if len(found) > 1:
        print(f"[WARN] একাধিক reference.* file পাওয়া গেছে {[str(f) for f in found]}, "
              f"'{source}' ব্যবহার করা হচ্ছে। বাকিগুলো সরিয়ে ফেলতে পারো।")

    if source.resolve() == FINAL_WAV.resolve() and source.suffix.lower() == ".wav":
        # আগে থেকেই .wav, কিন্তু তারপরও canonical format-এ re-encode করে নিচ্ছি
        # (sample rate/channel/codec নিশ্চিত করতে), তাই আলাদা temp নাম ব্যবহার করা হচ্ছে
        tmp = VOICE_DIR / "_reference_source.wav"
        source.rename(tmp)
        source = tmp

    print(f"[1/2] পাওয়া গেছে: {source}")
    print(f"[2/2] Convert হচ্ছে -> {FINAL_WAV} (mono, 24kHz, 16-bit PCM)")

    cmd = [
        "ffmpeg", "-y",
        "-i", str(source),
        "-ac", "1",          # mono
        "-ar", "24000",      # F5-TTS-এর native sample rate-এর সাথে মিলিয়ে
        "-sample_fmt", "s16",
        str(FINAL_WAV),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr)
        raise SystemExit(f"[FAIL] ffmpeg convert করতে পারেনি {source} থেকে। উপরের error দেখো।")

    # মূল raw recording ফাইলটা মুছে ফেলা হচ্ছে যাতে দ্বিতীয়বার run-এ confuse না করে
    if source != FINAL_WAV:
        source.unlink(missing_ok=True)

    # কিছু sanity check — duration আর silence
    import soundfile as sf
    info = sf.info(str(FINAL_WAV))
    print(f"[OK] reference.wav তৈরি হয়েছে — duration: {info.duration:.1f}s, "
          f"sample_rate: {info.samplerate}, channels: {info.channels}")

    if info.duration < 3:
        print("[WARN] Reference audio ৩ সেকেন্ডের চেয়ে ছোট — অন্তত ৫-১৫ সেকেন্ড রাখা ভালো, "
              "নাহলে voice cloning quality খারাপ হতে পারে।")
    if info.duration > 20:
        print("[WARN] Reference audio ২০ সেকেন্ডের চেয়ে বড় — এটা ছোট করে ৫-১৫ সেকেন্ডে "
              "আনা ভালো, কারণ F5-TTS-এর single-generation-এ ৩০-সেকেন্ড limit আছে "
              "(reference + generated মিলিয়ে), লম্বা reference থাকলে generated অংশের জন্য "
              "জায়গা কমে যাবে।")


if __name__ == "__main__":
    main()
