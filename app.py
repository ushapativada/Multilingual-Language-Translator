# app.py - Main Flask Application
from flask import Flask, render_template, request, jsonify
from deep_translator import GoogleTranslator
from deep_translator.exceptions import LanguageNotSupportedException, TranslationNotFound
from langdetect import detect, detect_langs
from langdetect.lang_detect_exception import LangDetectException
import json
import os
from datetime import datetime

app = Flask(__name__)

# Language codes and names mapping                                                       
LANGUAGES = {
    'auto': 'Auto-detect',
    'en': 'English',
    'es': 'Spanish', 
    'fr': 'French',
    'de': 'German',
    'it': 'Italian',
    'pt': 'Portuguese',
    'ru': 'Russian',
    'ja': 'Japanese',
    'ko': 'Korean',
    'zh': 'Chinese (Simplified)',
    'ar': 'Arabic',
    'hi': 'Hindi',
    'tr': 'Turkish',
    'pl': 'Polish',
    'nl': 'Dutch',
    'sv': 'Swedish',
    'da': 'Danish',
    'no': 'Norwegian',
    'fi': 'Finnish'
}

# Store translation history (in production, use a database)
translation_history = []

def detect_language(text):
    """Detect language using langdetect library"""
    try:
        detected = detect(text)
        # Get confidence score
        langs = detect_langs(text)
        confidence = langs[0].prob if langs else 0.5
        return detected, confidence
    except LangDetectException:
        return 'en', 0.5  # Default to English if detection fails

@app.route('/')
def index():
    """Main page with translator interface"""
    return render_template('index.html', languages=LANGUAGES)

@app.route('/translate', methods=['POST'])
def translate_text():
    """API endpoint for translation"""
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        source_lang = data.get('source', 'auto')
        target_lang = data.get('target', 'en')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        if len(text) > 5000:
            return jsonify({'error': 'Text too long (max 5000 characters)'}), 400
        
        # Detect source language if auto-detect is selected
        if source_lang == 'auto':
            detected_lang, confidence = detect_language(text)
        else:
            detected_lang = source_lang
            confidence = 1.0
        
        # Don't translate if source and target are the same
        if detected_lang == target_lang:
            result = {
                'translated_text': text,
                'detected_language': detected_lang,
                'confidence': confidence,
                'source_lang': detected_lang,
                'target_lang': target_lang
            }
        else:
            # Perform translation using deep-translator
            translator = GoogleTranslator(source=detected_lang, target=target_lang)
            translated_text = translator.translate(text)
            
            result = {
                'translated_text': translated_text,
                'detected_language': detected_lang,
                'confidence': confidence,
                'source_lang': detected_lang,
                'target_lang': target_lang
            }
        
        # Add to history
        history_entry = {
            'timestamp': datetime.now().isoformat(),
            'original_text': text,
            'translated_text': result['translated_text'],
            'source_lang': result['source_lang'],
            'target_lang': result['target_lang']
        }
        translation_history.append(history_entry)
        
        # Keep only last 50 translations
        if len(translation_history) > 50:
            translation_history.pop(0)
        
        return jsonify(result)
    
    except LanguageNotSupportedException as e:
        return jsonify({'error': f'Language not supported: {str(e)}'}), 400
    except TranslationNotFound as e:
        return jsonify({'error': f'Translation not found: {str(e)}'}), 404
    except Exception as e:
        return jsonify({'error': f'Translation failed: {str(e)}'}), 500

@app.route('/detect', methods=['POST'])
def detect_language_endpoint():
    """API endpoint for language detection only"""
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        detected_lang, confidence = detect_language(text)
        return jsonify({
            'language': detected_lang,
            'confidence': confidence,
            'language_name': LANGUAGES.get(detected_lang, 'Unknown')
        })
        
    except Exception as e:
        return jsonify({'error': f'Detection failed: {str(e)}'}), 500

@app.route('/history')
def get_history():
    """Get translation history"""
    return jsonify(translation_history[-10:])  # Return last 10 translations

@app.route('/languages')
def get_languages():
    """Get available languages"""
    return jsonify(LANGUAGES)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)