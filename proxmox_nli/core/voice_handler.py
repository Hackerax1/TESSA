"""
Voice handler module for speech recognition and synthesis.
"""
import speech_recognition as sr
from gtts import gTTS
import tempfile
import os
import base64

class VoiceHandler:
    def __init__(self):
        """Initialize the voice handler"""
        self.recognizer = sr.Recognizer()
        
    def speech_to_text(self, audio_data):
        """
        Convert speech to text using Google Speech Recognition
        
        Args:
            audio_data: Base64 encoded audio data in WAV format
        
        Returns:
            dict: Contains recognized text or error message
        """
        try:
            # Decode base64 audio data
            audio_bytes = base64.b64decode(audio_data.split(',')[1])
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
                temp_file.write(audio_bytes)
                temp_file_path = temp_file.name
            
            # Read the audio file
            with sr.AudioFile(temp_file_path) as source:
                audio = self.recognizer.record(source)
            
            # Clean up temporary file
            os.unlink(temp_file_path)
            
            # Convert speech to text
            text = self.recognizer.recognize_google(audio)
            return {'success': True, 'text': text}
            
        except sr.UnknownValueError:
            return {'success': False, 'error': 'Could not understand audio'}
        except sr.RequestError as e:
            return {'success': False, 'error': f'Error with the speech recognition service: {str(e)}'}
        except Exception as e:
            return {'success': False, 'error': f'Error processing audio: {str(e)}'}

    def text_to_speech(self, text):
        """
        Convert text to speech using Google Text-to-Speech
        
        Args:
            text: Text to convert to speech
            
        Returns:
            dict: Contains base64 encoded audio data or error message
        """
        try:
            # Create a temporary file for the audio
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                # Generate speech
                tts = gTTS(text=text, lang='en')
                tts.save(temp_file.name)
                
                # Read the audio file and encode to base64
                with open(temp_file.name, 'rb') as audio_file:
                    audio_data = base64.b64encode(audio_file.read()).decode('utf-8')
                
                # Clean up temporary file
                os.unlink(temp_file.name)
                
                return {
                    'success': True,
                    'audio': f'data:audio/mp3;base64,{audio_data}'
                }
                
        except Exception as e:
            return {'success': False, 'error': f'Error generating speech: {str(e)}'}