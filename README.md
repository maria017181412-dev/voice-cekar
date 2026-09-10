# F5-TTS Spike Test — শুধু feasibility test করার জন্য একটা আলাদা প্রজেক্ট

এটা তোমার আসল yt-core প্রজেক্ট না — এটা একটা সম্পূর্ণ আলাদা, ছোট, isolated প্রজেক্ট যেটা দিয়ে
শুধু একটা প্রশ্নের real answer বের করা হবে: **GitHub-এর ফ্রি CPU runner দিয়ে F5-TTS ব্যবহার করে
বাস্তবে reasonable সময়ে voice-over বানানো সম্ভব কিনা।** ফলাফল ভালো হলে, তখন এই design আসল
প্রজেক্টে (Section C, আগের audit report) নিয়ে যাওয়া হবে।

কোনো API key/secret লাগে না — সবকিছু ফ্রি, GitHub Actions-এর মধ্যেই।

---

## ১. কোথায় কী রাখবে

| জিনিস | কোথায় | নোট |
|---|---|---|
| **Voice-over-এর টেক্সট** | `input/script.txt` | placeholder টেক্সট মুছে নিজের script paste করো |
| **Reference voice (যে কণ্ঠে বানাতে চাও)** | `voices/narrator/reference.<যেকোনো ফরম্যাট>` | phone-এ যেভাবেই record করেছো (m4a/mp3/যা-ই হোক), নাম "reference" দিয়ে শুরু হলেই হবে — workflow নিজেই wav-এ convert করে নেয় |
| **Reference voice-এর transcript** | `voices/narrator/reference.txt` | নিচের ভাষা/sentence অংশ দেখো |
| **চূড়ান্ত audio (output)** | GitHub-এর **Actions run → Artifacts** section-এ | নিচে ধাপ ৪ দেখো, ডাউনলোড লিংক ওখানেই পাবে |

`voices/narrator/PLACEHOLDER_README.txt` ফাইলে বিস্তারিত লেখা আছে reference audio নিয়ে।

### Reference voice — কোন ভাষায়, আর কী বলবে

**ইংরেজিতে record করো, বাংলায় না।** তোমার আসল yt-core প্রজেক্ট ইংরেজি ভাষায় narration বানায় (config-এ `"language": "en"`), আর F5-TTS-এর base model মূলত ইংরেজি/চীনা ভাষার উপর train করা — reference voice টার্গেট ভাষার সাথে না মিললে pronunciation/accent অস্বাভাবিক শোনাতে পারে।

Phone-এর Voice Recorder/Voice Memos app খুলে, স্বাভাবিক, শান্ত গলায় (narration-এর মতো টোন) নিচের বাক্যটা জোরে পড়ো, ~৮-১২ সেকেন্ড লাগবে:

> "This is a short voice sample. I'm recording it so the system can learn the natural tone and pace of my narration voice, calm and steady, just like a story being told at night."

এই একই বাক্যটা হুবহু কপি করে `voices/narrator/reference.txt`-এ বসিয়ে দাও — নিজে কান দিয়ে শুনে transcribe করার দরকার নেই।

---

## ২. GitHub-এ কীভাবে বসাবে (নতুন account-এ)

1. নতুন account-এ একটা **public** repo বানাও। Public হওয়া জরুরি — তাহলেই Actions minutes সম্পূর্ণ ফ্রি।
2. Settings → Actions → General → "Workflow permissions" → **"Read and write permissions"** বেছে Save করো।
3. **Add file → Create new file** দিয়ে শুধু একটা ফাইল বানাও: path `.github/workflows/00-unpack-zip.yml`, ভেতরে এই zip-এর সেই ফাইলের content বসাও, Commit করো।
4. **Add file → Upload files** দিয়ে পুরো zip-টা repo-র root-এ upload করে Commit করো — এই push-ই বাকি সব ফাইল (workflows, scripts, README) automatically extract করে repo-তে বসিয়ে দেবে।
5. `voices/narrator/` ফোল্ডারে তোমার reference recording + `reference.txt` যোগ করো (উপরের অংশ দেখো), আর `input/script.txt`-এ নিজের test script বসাও, তারপর commit/push করো।

---

## ৩. প্রথমে যেটা চালাবে: benchmark (আগে এটা, বাকি সব পরে)

GitHub repo-র **Actions** ট্যাবে যাও → বাম পাশে **"01 - Benchmark (single test, real CPU speed)"** workflow বেছে নাও → **Run workflow** বাটনে ক্লিক করো।

এটা মাত্র একটা বাক্য generate করবে আর সময় মাপবে। রান শেষ হলে (কয়েক মিনিট, বেশিরভাগ সময় model download/install-এ যাবে প্রথমবার):

- Run-এর নিচে **Artifacts** অংশে `benchmark-result` নামে একটা ফাইল পাবে — ডাউনলোড করে `timing_result.json` খুলো।
- ওখানে `real_time_factor_RTF` নামে একটা সংখ্যা পাবে। এটাই আসল উত্তর।

**RTF দিয়ে বোঝার নিয়ম:**
- RTF = ৫ মানে, ১ সেকেন্ড audio বানাতে ৫ সেকেন্ড সময় লাগে
- ৬০ মিনিট (৩৬০০ সেকেন্ড) audio বানাতে মোট সময় ≈ RTF × ৩৬০০ সেকেন্ড, তারপর সেটাকে shard সংখ্যা দিয়ে ভাগ করলে বাস্তব wall-clock সময় পাওয়া যাবে (ধাপ ৪ দেখো)।

এই সংখ্যাটা আমাকে পাঠিয়ো (`timing_result.json`-এর পুরো content) — আমি হিসেব করে বলে দেবো ৬০-৯০ মিনিটের long-form-এর জন্য কতগুলো shard দরকার হবে, আর এটা আদৌ বাস্তবসম্মত কিনা।

---

## ৪. তারপর পুরো script generate করে দেখা

Actions ট্যাবে **"02 - Generate voice-over (parallel CPU shards)"** workflow বেছে নাও → **Run workflow** → `shard_count` ঘরে একটা সংখ্যা দাও (ছোট script-এ ৩-৫ যথেষ্ট; লম্বা script-এ ১০-২০ দিয়ে শুরু করো, benchmark-এর ফলাফল অনুযায়ী পরে adjust করবো) → Run।

এই workflow ৩টা ধাপে চলে (Actions run পেজে সবগুলো দেখতে পাবে):
1. **prepare** — script-টা ছোট ছোট chunk-এ ভাগ করে (F5-TTS-এর ৩০-সেকেন্ড limit মাথায় রেখে)
2. **generate** — তোমার দেওয়া shard সংখ্যা অনুযায়ী সমান্তরালে (parallel) সবগুলো chunk বানায়
3. **stitch** — সব chunk জোড়া লাগিয়ে একটা final.wav বানায়, আর কোনো chunk miss/fail করলে স্পষ্ট report দেয়

**Output কোথায়:** run শেষ হলে Artifacts section-এ `final-voice-over` নামে একটা ফাইল পাবে — তার ভেতরে:
- `final.wav` — পুরো voice-over
- `generation_report.json` — কতগুলো chunk সফল হলো, কতগুলো fail/missing হলো, মোট audio কত সেকেন্ড

---

## ৫. আমাকে কী পাঠাবে

- `timing_result.json` (ধাপ ৩ থেকে) — সবার আগে এটা
- `generation_report.json` (ধাপ ৪ থেকে) — কতগুলো chunk fail হলো
- পুরো Actions run-এর মোট সময় কত লাগলো (run পেজের উপরে দেখা যায়) — বিশেষ করে `generate` job-এর wall-clock time
- চাইলে `final.wav`-টাও পাঠাতে পারো, শুনে quality/naturalness নিয়ে মতামত দেবো

এই সংখ্যাগুলো পেলে আমি বলে দেবো:
- ৬০-৯০ মিনিটের `historysleep`-এর মতো channel-এর জন্য এই approach বাস্তবসম্মত কিনা
- হলে কতগুলো shard লাগবে বাস্তবে
- না হলে বিকল্প কী (target duration কমানো, chunk সাইজ আরও ছোট করা, ইত্যাদি)

কিছু ঠিকঠাক কাজ করলে, তখনই এই design-টা আসল yt-core প্রজেক্টে নিয়ে যাওয়ার implementation শুরু করবো — এখানে যা কিছু ঘটুক, তোমার আসল প্রজেক্টের কিছুই ছোঁয়া হচ্ছে না।
