এই folder-এ দুটো ফাইল দরকার, দুটোই তোমাকে যোগ করতে হবে (এখানে কোনো audio অন্তর্ভুক্ত করা হয়নি):

1. reference.wav
   - ৫-১৫ সেকেন্ড, একজন মানুষের কণ্ঠ, পরিষ্কার (background noise/music ছাড়া)
   - mono বা stereo দুটোই চলবে, কোনো clipping/distortion থাকা যাবে না
   - যে voice-এ F5-TTS narration বানাতে চাও, ঠিক সেই কণ্ঠের sample

2. reference.txt
   - reference.wav-এ ঠিক যা বলা হয়েছে তার হুবহু transcript, plain text, এক লাইনে
   - ভুল transcript দিলে generated audio-র quality খারাপ হবে

দুটো ফাইল যোগ করার পর এই PLACEHOLDER_README.txt ফাইলটা মুছে ফেলতে পারো।
