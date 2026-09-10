"""
একটা shard-এর জন্য নির্ধারিত chunk গুলো generate করে।

Usage:
    python scripts/generate_chunk.py <shard_index> <shard_count>

chunks/manifest.json থেকে chunk_id-র উপর ভিত্তি করে ভাগ করা হয়
(chunk_id % shard_count == shard_index) — প্রতিটা shard job নিজের
ভাগটুকু নেয়, model শুধু একবার load করে সবগুলো chunk-এ loop করে,
যাতে বারবার model reload-এর খরচ না লাগে।

প্রতিটা chunk আলাদাভাবে retry হয় (fail করলে ৩ বার পর্যন্ত) — একটা
chunk fail করলে পুরো shard job crash করবে না, বাকি chunk গুলো চলতে থাকবে।

Output: output/chunks/chunk_XXXX.wav + output/chunks/status_shard_<N>.json
"""

import json
import sys
import time
from pathlib import Path

REF_AUDIO = Path("voices/narrator/reference.wav")
REF_TEXT_FILE = Path("voices/narrator/reference.txt")
OUT_DIR = Path("output/chunks")
MAX_RETRIES = 3


def main():
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python scripts/generate_chunk.py <shard_index> <shard_count>")
    shard_index = int(sys.argv[1])
    shard_count = int(sys.argv[2])

    if not REF_AUDIO.exists() or not REF_TEXT_FILE.exists():
        raise SystemExit("[FAIL] voices/narrator/reference.wav এবং reference.txt দুটোই দরকার।")

    manifest_path = Path("chunks/manifest.json")
    if not manifest_path.exists():
        raise SystemExit("[FAIL] chunks/manifest.json পাওয়া যায়নি — প্রথমে chunk_text.py চালাও।")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    my_chunks = [c for c in manifest if int(c["chunk_id"]) % shard_count == shard_index]

    print(f"[shard {shard_index}/{shard_count}] এই shard-এর জন্য {len(my_chunks)}টা chunk বরাদ্দ।")
    if not my_chunks:
        print("এই shard-এ কোনো chunk নেই, কিছু করার নেই।")
        return

    import soundfile as sf
    from f5_tts.api import F5TTS

    ref_text = REF_TEXT_FILE.read_text(encoding="utf-8").strip()

    print("Model লোড হচ্ছে (একবারই, পুরো shard-এর জন্য)...")
    load_start = time.time()
    f5tts = F5TTS(model="F5TTS_v1_Base")
    load_elapsed = time.time() - load_start
    print(f"    model load: {load_elapsed:.2f}s")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    status = []

    for c in my_chunks:
        chunk_id = c["chunk_id"]
        text = Path(c["text_path"]).read_text(encoding="utf-8").strip()
        out_path = OUT_DIR / f"chunk_{chunk_id}.wav"

        attempt = 0
        ok = False
        last_error = None
        gen_seconds = None
        while attempt < MAX_RETRIES and not ok:
            attempt += 1
            try:
                start = time.time()
                wav, sr, _spec = f5tts.infer(
                    ref_file=str(REF_AUDIO),
                    ref_text=ref_text,
                    gen_text=text,
                    seed=0,
                )
                gen_seconds = time.time() - start
                sf.write(str(out_path), wav, sr)
                ok = True
                print(f"  chunk {chunk_id}: OK ({gen_seconds:.1f}s, চেষ্টা {attempt})")
            except Exception as e:  # noqa: BLE001 — ইচ্ছাকৃতভাবে broad, প্রতিটা chunk আলাদা retry করার জন্য
                last_error = str(e)
                print(f"  chunk {chunk_id}: FAIL চেষ্টা {attempt}/{MAX_RETRIES} -> {last_error}")

        status.append({
            "chunk_id": chunk_id,
            "generation_status": "ok" if ok else "failed",
            "attempts": attempt,
            "generation_seconds": round(gen_seconds, 2) if gen_seconds else None,
            "audio_path": str(out_path) if ok else None,
            "error": None if ok else last_error,
        })

    status_path = OUT_DIR / f"status_shard_{shard_index}.json"
    status_path.write_text(json.dumps(status, indent=2, ensure_ascii=False), encoding="utf-8")

    failed = [s for s in status if s["generation_status"] == "failed"]
    print(f"\n[shard {shard_index}] শেষ: {len(status) - len(failed)} সফল, {len(failed)} ব্যর্থ।")
    if failed:
        # non-zero exit যাতে GitHub Actions-এর summary-তে shard-টা লাল দেখায় —
        # কিন্তু বাকি shard গুলো এতে আটকাবে না, প্রতিটা matrix job আলাদা।
        print("[WARN] কিছু chunk বারবার fail করেছে, status file-এ বিস্তারিত আছে।")
        sys.exit(1)


if __name__ == "__main__":
    main()
