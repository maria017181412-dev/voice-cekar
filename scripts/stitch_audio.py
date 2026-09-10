"""
সব shard-এর generate করা chunk_XXXX.wav ফাইলগুলোকে সঠিক ক্রমে জোড়া লাগিয়ে
একটা final.wav বানায়, এবং কোনো chunk missing/failed থাকলে স্পষ্টভাবে report করে
(চুপচাপ skip করে না)।

Output:
    output/final.wav
    output/generation_report.json
"""

import json
import subprocess
import sys
from pathlib import Path

CHUNKS_DIR = Path("output/chunks")
OUT_DIR = Path("output")


def main():
    manifest_path = Path("chunks/manifest.json")
    if not manifest_path.exists():
        raise SystemExit("[FAIL] chunks/manifest.json পাওয়া যায়নি।")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_ids = [c["chunk_id"] for c in manifest]

    # সব shard-এর status_shard_*.json একত্র করা
    all_status = []
    for status_file in sorted(CHUNKS_DIR.glob("status_shard_*.json")):
        all_status.extend(json.loads(status_file.read_text(encoding="utf-8")))
    status_by_id = {s["chunk_id"]: s for s in all_status}

    present_wavs = {p.stem.replace("chunk_", ""): p for p in CHUNKS_DIR.glob("chunk_*.wav")}

    missing = [cid for cid in expected_ids if cid not in present_wavs]
    failed = [cid for cid in expected_ids if status_by_id.get(cid, {}).get("generation_status") == "failed"]

    if missing:
        print(f"[WARN] {len(missing)}টা chunk-এর audio file একেবারেই পাওয়া যায়নি: {missing}")
    if failed:
        print(f"[WARN] {len(failed)}টা chunk status অনুযায়ী failed: {failed}")

    ordered_ids = [cid for cid in expected_ids if cid in present_wavs]
    if not ordered_ids:
        raise SystemExit("[FAIL] একটাও chunk audio পাওয়া যায়নি, stitch করার কিছু নেই।")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    concat_list = OUT_DIR / "concat_list.txt"
    with concat_list.open("w", encoding="utf-8") as f:
        for cid in ordered_ids:
            wav_path = present_wavs[cid].resolve()
            f.write(f"file '{wav_path.as_posix()}'\n")

    final_path = OUT_DIR / "final.wav"
    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat_list), "-c", "copy", str(final_path),
    ]
    print("চলছে:", " ".join(cmd))
    subprocess.run(cmd, check=True)

    # final duration মাপা
    import soundfile as sf
    info = sf.info(str(final_path))

    report = {
        "expected_chunks": len(expected_ids),
        "generated_chunks": len(ordered_ids),
        "missing_chunk_ids": missing,
        "failed_chunk_ids": failed,
        "final_audio_seconds": round(info.duration, 2),
        "final_audio_path": str(final_path),
        "complete": len(missing) == 0 and len(failed) == 0,
    }
    (OUT_DIR / "generation_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))

    if not report["complete"]:
        print("[WARN] পুরো narration সম্পূর্ণ হয়নি — কিছু chunk অনুপস্থিত/ব্যর্থ। "
              "output/generation_report.json দেখো।")
        sys.exit(1)


if __name__ == "__main__":
    main()
