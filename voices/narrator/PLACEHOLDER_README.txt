এই folder-এ দুটো জিনিস দরকার (কোনো audio এখানে অন্তর্ভুক্ত করা হয়নি, তোমাকে যোগ করতে হবে):

1. reference.<যেকোনো ফরম্যাট> — যেমন reference.m4a, reference.mp3, reference.3gp
   - phone-এর default Voice Recorder / Voice Memos app দিয়ে record করলেই যথেষ্ট,
     আলাদা কোনো converter app/website লাগবে না — workflow নিজেই ffmpeg দিয়ে
     এটাকে reference.wav-এ convert করে নেবে (scripts/prepare_reference.py)।
   - ৫-১৫ সেকেন্ড, পরিষ্কার কণ্ঠ, background noise/music ছাড়া
   - নামটা অবশ্যই "reference" দিয়ে শুরু হতে হবে (extension যা-ই হোক)

2. reference.txt
   - উপরের recording-এ ঠিক যা বলা হয়েছে তার হুবহু transcript, plain text, এক লাইনে
   - সহজ করার জন্য: প্রধান README.md-এ একটা fixed sentence দেওয়া আছে —
     সেটাই জোরে পড়ে record করো, তাহলে reference.txt-এ সেই একই sentence
     copy-paste করলেই হবে, আলাদা করে কান দিয়ে transcribe করতে হবে না।

দুটো যোগ করার পর এই ফাইলটা (PLACEHOLDER_README.txt) মুছে ফেলতে পারো।
