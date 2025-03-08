"""
Voice handler module for speech recognition and synthesis with personalized voice profiles.
"""
import speech_recognition as sr
from gtts import gTTS
import tempfile
import os
import base64
import json
import random
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Union

@dataclass
class VoiceProfile:
    """Voice profile settings for TTS customization"""
    name: str
    lang: str = "en"
    tld: str = "com"  # Accent/region (com, co.uk, com.au, ca, co.in, ie, co.za)
    slow: bool = False  # Speech pace
    pitch: float = 1.0  # Voice pitch (requires additional TTS engine)
    volume: float = 1.0  # Voice volume (requires additional TTS engine)
    tone_style: str = "friendly"  # friendly, professional, casual, enthusiastic
    
    def to_dict(self):
        """Convert profile to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data):
        """Create profile from dictionary"""
        return cls(**data)

class VoiceHandler:
    def __init__(self):
        """Initialize the voice handler"""
        self.recognizer = sr.Recognizer()
        self.profiles_dir = Path(__file__).parent.parent.parent / "data" / "voice_profiles"
        self.profiles_dir.mkdir(exist_ok=True, parents=True)
        
        # Default profiles
        self.default_profiles = {
            "tessa_default": VoiceProfile(
                name="TESSA Default",
                lang="en",
                tld="com",
                slow=False,
                pitch=1.0,
                volume=1.0,
                tone_style="friendly"
            ),
            "tessa_warm": VoiceProfile(
                name="TESSA Warm",
                lang="en",
                tld="com.au",  # Australian accent is often perceived as warm
                slow=True,
                pitch=1.05,
                volume=1.0,
                tone_style="enthusiastic"
            ),
            "tessa_professional": VoiceProfile(
                name="TESSA Professional",
                lang="en",
                tld="co.uk",  # British accent for professional tone
                slow=False,
                pitch=0.98,
                volume=1.0,
                tone_style="professional"
            )
        }
        
        # Load or create profiles
        self.profiles = self._load_profiles()
        self.active_profile_name = "tessa_default"
        
        # Personality quirks/phrases by tone style
        self.personality_phrases = {
            "friendly": [
                "I'm happy to help with that!",
                "Consider it done!",
                "I enjoy helping with your homelab.",
                "That's an excellent choice.",
                "I've got this handled for you."
            ],
            "professional": [
                "Processing your request now.",
                "I'll manage that efficiently.",
                "Request confirmed.",
                "Executing your command promptly.",
                "I've noted your requirements."
            ],
            "casual": [
                "No problem, on it!",
                "Sure thing!",
                "You got it!",
                "Easy peasy!",
                "I'll take care of that real quick."
            ],
            "enthusiastic": [
                "Wonderful choice! Let's get that set up!",
                "I'm excited to help with this project!",
                "This is going to be great!",
                "I love working on this kind of task!",
                "Let's make some magic happen!"
            ]
        }
        
        # User experience level influences (0-beginner to 1-expert)
        self.user_experience_modifiers = {
            0.0: {  # Beginner
                "explanations": "detailed", 
                "terminology": "simple",
                "tone_style": "friendly"
            },
            0.3: {  # Casual user
                "explanations": "balanced",
                "terminology": "moderate",
                "tone_style": "casual"
            },
            0.7: {  # Advanced
                "explanations": "concise",
                "terminology": "technical",
                "tone_style": "professional" 
            },
            1.0: {  # Expert
                "explanations": "minimal",
                "terminology": "expert",
                "tone_style": "professional"
            }
        }
        
    def _load_profiles(self) -> Dict[str, VoiceProfile]:
        """Load voice profiles from disk or use defaults"""
        profiles = self.default_profiles.copy()
        
        # Load any custom profiles from disk
        for profile_file in self.profiles_dir.glob("*.json"):
            try:
                with open(profile_file, "r") as f:
                    profile_data = json.load(f)
                    profile = VoiceProfile.from_dict(profile_data)
                    profiles[profile_file.stem] = profile
            except Exception as e:
                print(f"Error loading profile {profile_file}: {e}")
                
        return profiles
        
    def save_profile(self, profile_name: str, profile: VoiceProfile):
        """Save a voice profile to disk"""
        profile_path = self.profiles_dir / f"{profile_name}.json"
        
        with open(profile_path, "w") as f:
            json.dump(profile.to_dict(), f, indent=2)
            
        # Update in-memory profiles
        self.profiles[profile_name] = profile
        
    def set_active_profile(self, profile_name: str):
        """Set the active voice profile"""
        if profile_name in self.profiles:
            self.active_profile_name = profile_name
            return True
        return False
        
    def get_active_profile(self) -> VoiceProfile:
        """Get the current active voice profile"""
        return self.profiles[self.active_profile_name]
    
    def list_profiles(self) -> List[str]:
        """List all available voice profiles"""
        return list(self.profiles.keys())
    
    def adapt_to_user_experience(self, experience_level: float):
        """
        Adapt TESSA's voice to user experience level
        
        Args:
            experience_level: Float from 0.0 (beginner) to 1.0 (expert)
        """
        # Find the closest experience level
        levels = sorted(self.user_experience_modifiers.keys())
        closest_level = min(levels, key=lambda x: abs(x - experience_level))
        
        # Get the profile modifiers
        modifiers = self.user_experience_modifiers[closest_level]
        
        # Select appropriate profile based on modifiers
        if modifiers["tone_style"] == "friendly":
            self.set_active_profile("tessa_warm")
        elif modifiers["tone_style"] == "professional":
            self.set_active_profile("tessa_professional")
        else:
            self.set_active_profile("tessa_default")
        
    def add_personality(self, text: str, probability: float = 0.2) -> str:
        """
        Add personality quirks to responses
        
        Args:
            text: The text to potentially modify
            probability: Chance (0-1) of adding a personality phrase
            
        Returns:
            str: Text with personality additions
        """
        if random.random() > probability:
            return text
            
        profile = self.get_active_profile()
        tone_style = profile.tone_style
        
        # Select a random phrase for the current tone style
        phrases = self.personality_phrases.get(tone_style, self.personality_phrases["friendly"])
        personality_phrase = random.choice(phrases)
        
        # Add the phrase to the beginning or end of the text
        if random.random() > 0.5:
            return f"{personality_phrase} {text}"
        else:
            return f"{text} {personality_phrase}"
        
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

    def text_to_speech(self, text, add_personality=True):
        """
        Convert text to speech using Google Text-to-Speech
        with customizable voice profile
        
        Args:
            text: Text to convert to speech
            add_personality: Whether to add personality quirks
            
        Returns:
            dict: Contains base64 encoded audio data or error message
        """
        try:
            # Apply personality if enabled
            if add_personality:
                text = self.add_personality(text)
                
            # Get active profile
            profile = self.get_active_profile()
            
            # Create a temporary file for the audio
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                # Generate speech with profile settings
                tts = gTTS(
                    text=text, 
                    lang=profile.lang, 
                    tld=profile.tld,
                    slow=profile.slow
                )
                tts.save(temp_file.name)
                
                # Read the audio file and encode to base64
                with open(temp_file.name, 'rb') as audio_file:
                    audio_data = base64.b64encode(audio_file.read()).decode('utf-8')
                
                # Clean up temporary file
                os.unlink(temp_file.name)
                
                return {
                    'success': True,
                    'audio': f'data:audio/mp3;base64,{audio_data}',
                    'text': text,  # Return the potentially modified text
                    'profile': profile.name
                }
                
        except Exception as e:
            return {'success': False, 'error': f'Error generating speech: {str(e)}'}