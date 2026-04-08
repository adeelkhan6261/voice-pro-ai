import os
import asyncio
import json
import uuid
from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS
from engine import VoiceEngine

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

# Force the output directory to be relative to the app
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

CUSTOM_VOICES_FILE = os.path.join(os.path.dirname(__file__), "custom_voices.json")
CLONED_DIR = os.path.join(app.static_folder, "audio", "cloned")
os.makedirs(CLONED_DIR, exist_ok=True)

voice_engine = VoiceEngine(output_dir=OUTPUT_DIR)

@app.route('/')
def index():
    return render_template('index.html')

def load_custom_voices():
    if os.path.exists(CUSTOM_VOICES_FILE):
        with open(CUSTOM_VOICES_FILE, "r") as f:
            return json.load(f)
    return []

def save_custom_voice(name, filename, gender):
    voices = load_custom_voices()
    voices.append({
        "name": name, 
        "value": f"custom_{filename}", 
        "path": filename,
        "gender": gender
    })
    with open(CUSTOM_VOICES_FILE, "w") as f:
        json.dump(voices, f)

@app.route('/api/generate', methods=['POST'])
def generate():
    data = request.json
    text = data.get('text', '')
    voice = data.get('voice', 'ur-PK-AsadNeural')
    rate = data.get('rate', '+0%')
    pitch = data.get('pitch', '+0Hz')
    
    if not text:
        return jsonify({"error": "No text provided"}), 400
    
    # --- Smart Gender Matching for Custom Voices ---
    if voice.startswith("custom_"):
        # Find the gender metadata for this voice
        voices = load_custom_voices()
        v_data = next((v for v in voices if v['value'] == voice), None)
        
        if v_data and v_data.get('gender') == 'male':
            voice = "en-US-AndrewNeural" # High-quality Male Fallback
        else:
            voice = "en-US-AvaNeural" # High-quality Female Fallback
    
    # Unique filename for the output
    filename = f"voice_{uuid.uuid4().hex}.mp3"
    
    # Run async engine.speak in sync Flask
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        final_path = loop.run_until_complete(voice_engine.speak(text, voice, filename, rate, pitch))
        loop.close()
        
        if final_path:
            return jsonify({
                "success": True,
                "audio_url": f"/outputs/{filename}",
                "filename": filename
            })
        else:
            return jsonify({"error": "Failed to generate audio"}), 500
    except Exception as e:
        import traceback
        traceback.print_exc() # Print full error to console
        return jsonify({"error": str(e)}), 500

@app.route('/outputs/<path:filename>')
def serve_output(filename):
    return send_from_directory(OUTPUT_DIR, filename)

@app.route('/api/voices', methods=['GET'])
def get_custom_voices():
    return jsonify(load_custom_voices())

@app.route('/api/voices/delete', methods=['POST'])
def delete_voice():
    data = request.json
    voice_val = data.get('voice_val')
    
    if not voice_val:
        return jsonify({"error": "No voice specified"}), 400
    
    voices = load_custom_voices()
    new_voices = []
    deleted = False
    
    for v in voices:
        if v['value'] == voice_val:
            # Delete sample file
            sample_path = os.path.join(CLONED_DIR, v['path'])
            if os.path.exists(sample_path):
                os.remove(sample_path)
            deleted = True
        else:
            new_voices.append(v)
    
    if deleted:
        with open(CUSTOM_VOICES_FILE, "w") as f:
            json.dump(new_voices, f)
        return jsonify({"success": True, "message": "Voice deleted successfully!"})
    
    return jsonify({"error": "Voice not found"}), 404

@app.route('/api/clone', methods=['POST'])
def clone_voice():
    if 'sample' not in request.files:
        return jsonify({"error": "No voice sample uploaded"}), 400
    
    name = request.form.get('name', 'My New Voice')
    gender = request.form.get('gender', 'female')
    file = request.files['sample']
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # Save to cloned directory
    temp_filename = f"cloned_{uuid.uuid4().hex}_{file.filename}"
    temp_path = os.path.join(CLONED_DIR, temp_filename)
    file.save(temp_path)

    # Persist metadata with Gender
    save_custom_voice(name, temp_filename, gender)

    return jsonify({
        "success": True, 
        "message": f"'{name}' ({gender}) added to your Studio list!",
        "voice": {"name": name, "value": f"custom_{temp_filename}"}
    })

if __name__ == '__main__':
    # Default port 5000
    app.run(debug=True, host='0.0.0.0', port=5000)
