import os
import librosa
import numpy as np
import requests
import json
from flask import Flask, request, render_template, jsonify, send_from_directory, redirect, url_for

app = Flask(__name__)

# Configure API keys - you'll need to get your own API key
AUDD_API_KEY = "23f8be055a73d048a6e630068adf2785"

@app.route('/favicon.ico')
def favicon():
    return redirect(url_for('static', filename='nigga.png'))

def recognize_song(file_path):
    """
    Recognize a song using the AudD API
    """
    try:
        with open(file_path, 'rb') as file:
            data = {
                'api_token': AUDD_API_KEY,
                'return': 'spotify,apple_music,deezer,lyrics',
            }
            files = {
                'file': file,
            }
            
            response = requests.post('https://api.audd.io/', data=data, files=files)
            result = response.json()
            
            if result['status'] == 'success' and result.get('result'):
                return {
                    'success': True,
                    'song_info': result['result']
                }
            else:
                return {
                    'success': False,
                    'error': "Song not recognized"
                }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def analyze_audio(file_path):
    """
    Analyze audio file to extract basic features
    """
    try:
        # Load audio file
        y, sr = librosa.load(file_path)
        
        # Extract features
        duration = librosa.get_duration(y=y, sr=sr)
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        
        # Extract chroma features for key detection
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
        chroma_mean = np.mean(chroma, axis=1)
        notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        key = notes[np.argmax(chroma_mean)]
        
        return {
            'success': True,
            'audio_features': {
                'duration': round(duration, 2),
                'tempo': round(tempo, 2),
                'estimated_key': key
            }
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and recognition"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'})
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'})
    
    # Save the uploaded file temporarily
    temp_path = 'temp_audio.mp3'
    file.save(temp_path)
    
    # Analyze audio features
    audio_features = analyze_audio(temp_path)
    
    # Recognize the song
    recognition_result = recognize_song(temp_path)
    
    # Clean up the temporary file
    os.remove(temp_path)
    
    # Combine results
    result = {
        'success': recognition_result['success'],
        'audio_features': audio_features.get('audio_features', {})
    }
    
    if recognition_result['success']:
        song_info = recognition_result['song_info']
        result['song_details'] = {
            'title': song_info.get('title', 'Unknown'),
            'artist': song_info.get('artist', 'Unknown'),
            'album': song_info.get('album', 'Unknown'),
            'release_date': song_info.get('release_date', 'Unknown'),
            'label': song_info.get('label', 'Unknown'),
            'lyrics': song_info.get('lyrics', None)
        }
        
        # Add streaming service links if available
        streaming_links = {}
        if 'spotify' in song_info:
            streaming_links['spotify'] = song_info['spotify'].get('external_urls', {}).get('spotify', '')
        
        if 'apple_music' in song_info:
            streaming_links['apple_music'] = song_info['apple_music'].get('url', '')
            
        if 'deezer' in song_info:
            streaming_links['deezer'] = song_info['deezer'].get('link', '')
            
        result['streaming_links'] = streaming_links
    else:
        result['error'] = recognition_result.get('error', 'Unknown error')
    
    return jsonify(result)

if __name__ == '__main__':
    
    
    app.run(debug=True)