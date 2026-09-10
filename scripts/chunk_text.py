"""
input/script.txt কে ছোট ছোট chunk-এ ভাগ করে।

F5-TTS-এর single-generation-এ একটা hard limit আছে: reference audio + generated
audio মিলিয়ে ৩০ সেকেন্ডের বেশি একবারে করা যায় না। তাই chunk সাইজ রক্ষণশীলভাবে
ছোট রাখা হয়েছে (default ৩৫ শব্দ), এবং কখনো sentence-এর মাঝখান থেকে কাটা হয় না।

Output: chunks/manifest.json + chunks/chunk_XXXX.txt
"""

import json
import re
from pathlib import Path

MAX_WORDS_PER_CHUNK = 35  # রক্ষণশীল — ৩০ সেকেন্ড cap-এর ভেতরে নিরাপদে থাকার জন্য


def split_sentences(text: str):
    text = re.sub(r"\s+", " ", text).strip()
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [p.strip() for p in parts if p.strip()]


def pack_chunks(sentences, max_words):
    chunks = []
    current, current_words = [], 0
    for sent in sentences:
        n = len(sent.split())
        if current and current_words + n > max_words:
            chunks.append(" ".join(current))
            current, current_words = [], 0
        # একটা একক sentence-ই max_words-এর চেয়ে লম্বা হলে, সেটাকে আর ভাঙা হচ্ছে না —
        # শুধু warning print করা হবে, কারণ sentence-এর মাঝখান থেকে কাটা ঠিক না।
        current.append(sent)
        current_words += n
    if current:
        chunks.append(" ".join(current))
    return chunks


def main():
    script_path = Path("input/script.txt")
    if not script_path.exists():
        raise SystemExit(f"[FAIL] {script_path} পাওয়া যায়নি — এখানে তোমার script text রাখো।")

    text = script_path.read_text(encoding="utf-8")
    sentences = split_sentences(text)
    if not sentences:
        raise SystemExit("[FAIL] input/script.txt খালি বা পড়া যাচ্ছে না।")

    chunks = pack_chunks(sentences, MAX_WORDS_PER_CHUNK)

    for c in chunks:
        wc = len(c.split())
        if wc > MAX_WORDS_PER_CHUNK:
            print(f"[WARN] একটা একক sentence {wc} শব্দ লম্বা (limit {MAX_WORDS_PER_CHUNK}) — "
                  f"F5-TTS-এর ৩০-সেকেন্ড cap ছুঁয়ে ফেলতে পারে: {c[:80]}...")

    out_dir = Path("chunks")
    out_dir.mkdir(exist_ok=True)
    manifest = []
    for i, chunk in enumerate(chunks):
        chunk_id = f"{i:04d}"
        chunk_path = out_dir / f"chunk_{chunk_id}.txt"
        chunk_path.write_text(chunk, encoding="utf-8")
        manifest.append({
            "chunk_id": chunk_id,
            "text_path": f"chunks/chunk_{chunk_id}.txt",
            "word_count": len(chunk.split()),
        })

    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"[OK] মোট {len(chunks)}টা chunk তৈরি হয়েছে -> chunks/manifest.json")


if __name__ == "__main__":
    main()
