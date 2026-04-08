import asyncio
import edge_tts
import os
import re
import subprocess
import uuid
from TTS.api import TTS

class VoiceEngine:
    def __init__(self, output_dir="outputs", temp_dir="static/audio/temp", cloned_dir="static/audio/cloned"):
        self.output_dir = output_dir
        self.temp_dir = temp_dir
        self.cloned_dir = cloned_dir
        # Ensure absolute paths for system operations
        self.abs_output_dir = os.path.abspath(output_dir)
        self.abs_temp_dir = os.path.abspath(temp_dir)
        self.abs_cloned_dir = os.path.abspath(cloned_dir)
        
        os.makedirs(self.abs_output_dir, exist_ok=True)
        os.makedirs(self.abs_temp_dir, exist_ok=True)

        # Initialize XTTS v2 for 100% Accuracy (CPU Mode)
        print("🧬 Loading XTTS v2 AI Engine (CPU)... This may take a moment.")
        try:
            # This will download the model (~1.8GB) on the first run
            self.tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to("cpu")
            print("✅ Real Cloning Engine Initialized.")
        except Exception as e:
            print(f"⚠️ XTTS Init Error: {e}")
            self.tts = None

    def split_text(self, text, max_chars=800):
        """Splits text into manageable chunks for TTS engine."""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) < max_chars:
                current_chunk += " " + sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return [c for c in chunks if c]

    async def speak(self, text, voice="ur-PK-AsadNeural", output_name="final_output.mp3", rate="+0%", pitch="+0Hz"):
        # 🧪 Handle Real Cloning with XTTS v2
        if voice.startswith("custom_") and self.tts:
            print(f"🧬 Real Cloning Detected: Analyzing pattern for '{voice}'...")
            try:
                # 1. Find the sample path for this voice
                # We expect the voice ID to match a file in static/audio/cloned
                sample_filename = voice.replace("custom_", "")
                speaker_wav_path = os.path.join(self.abs_cloned_dir, sample_filename)
                
                if not os.path.exists(speaker_wav_path):
                    raise Exception(f"Sample file not found: {speaker_wav_path}")

                final_output_path = os.path.join(self.abs_output_dir, output_name)
                
                # 2. Generate with XTTS (Runs on CPU)
                # We generate to a temporary wav then convert to mp3
                temp_wav = os.path.join(self.abs_temp_dir, f"temp_{uuid.uuid4().hex}.wav")
                
                self.tts.tts_to_file(
                    text=text,
                    speaker_wav=speaker_wav_path,
                    language="en", # Default to English for now, XTTS auto-detects English/Urdu well
                    file_path=temp_wav
                )
                
                # 3. Convert to MP3
                cmd = f'ffmpeg -y -i "{temp_wav}" -codec:a libmp3lame -qscale:a 2 "{final_output_path}"'
                subprocess.run(cmd, shell=True, check=True, capture_output=True)
                
                # Cleanup
                if os.path.exists(temp_wav): os.remove(temp_wav)
                
                return final_output_path
            except Exception as e:
                print(f"❌ XTTS Generation Error: {e}. Falling back to standard engine.")
                voice = "en-US-AvaNeural" # Fallback

        # 🎙️ Handle Standard Voices with Edge-TTS
        if rate == "0%": rate = "+0%"
        if pitch == "0Hz": pitch = "+0Hz"
        
        chunks = self.split_text(text)
        temp_files = []
        session_id = uuid.uuid4().hex
        
        for i, chunk in enumerate(chunks):
            temp_file_name = f"{session_id}_chunk_{i}.mp3"
            temp_file_path = os.path.join(self.abs_temp_dir, temp_file_name)
            
            try:
                communicate = edge_tts.Communicate(text=chunk, voice=voice, rate=rate, pitch=pitch)
                await communicate.save(temp_file_path)
                temp_files.append(temp_file_path)
            except Exception as e:
                print(f"Error in edge-tts chunk {i}: {e}")
                raise e

        if not temp_files:
            return None

        list_file_path = os.path.join(self.abs_temp_dir, f"{session_id}_list.txt")
        with open(list_file_path, "w", encoding="utf-8") as f:
            for tf in temp_files:
                fname = os.path.basename(tf)
                f.write(f"file '{fname}'\n")

        final_path = os.path.join(self.abs_output_dir, output_name)
        try:
            cmd = f'ffmpeg -y -f concat -safe 0 -i "{os.path.basename(list_file_path)}" -c copy "{final_path}"'
            subprocess.run(cmd, shell=True, check=True, capture_output=True, cwd=self.abs_temp_dir)
        finally:
            for tf in temp_files:
                try: os.remove(tf)
                except: pass
            try: os.remove(list_file_path)
            except: pass

        return final_path
