"""
Voice handler module for speech recognition and synthesis with personalized voice profiles.
Includes voice authentication, wake word detection, and multi-language support.
"""
import speech_recognition as sr
from gtts import gTTS
import tempfile
import os
import base64
import json
import random
import numpy as np
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Union, Set, Tuple
import logging
from datetime import datetime, timedelta
import threading
import time
# For voice authentication
from scipy.io import wavfile
from scipy import signal
import librosa
import librosa.feature
import pickle

logger = logging.getLogger(__name__)

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

@dataclass
class VoiceShortcut:
    """Custom voice shortcut for quick command execution"""
    phrase: str
    command: str
    description: str
    user_id: Optional[str] = None  # If None, available to all users
    
    def to_dict(self):
        """Convert shortcut to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data):
        """Create shortcut from dictionary"""
        return cls(**data)

@dataclass
class CommandSequence:
    """Context-aware command sequence definition"""
    name: str
    triggers: List[str]
    steps: List[str]
    context_requirements: Dict[str, str] = field(default_factory=dict)
    user_id: Optional[str] = None  # If None, available to all users
    
    def to_dict(self):
        """Convert command sequence to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data):
        """Create command sequence from dictionary"""
        return cls(**data)

@dataclass
class VoiceSignature:
    """Voice fingerprint for user authentication"""
    user_id: str
    features: List[np.ndarray]
    created_at: str  # ISO format timestamp
    updated_at: str  # ISO format timestamp
    
    def to_dict(self):
        """Convert voice signature to dictionary"""
        return {
            "user_id": self.user_id,
            "features": [f.tolist() for f in self.features],
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create voice signature from dictionary"""
        return cls(
            user_id=data["user_id"],
            features=[np.array(f) for f in data["features"]],
            created_at=data["created_at"],
            updated_at=data["updated_at"]
        )

class VoiceHandler:
    def __init__(self):
        """Initialize the voice handler"""
        self.recognizer = sr.Recognizer()
        self.profiles_dir = Path(__file__).parent.parent.parent / "data" / "voice_profiles"
        self.profiles_dir.mkdir(exist_ok=True, parents=True)
        
        # Create directories for new features
        self.voice_auth_dir = Path(__file__).parent.parent.parent / "data" / "voice_auth"
        self.voice_auth_dir.mkdir(exist_ok=True, parents=True)
        
        self.shortcuts_dir = Path(__file__).parent.parent.parent / "data" / "voice_shortcuts"
        self.shortcuts_dir.mkdir(exist_ok=True, parents=True)
        
        self.sequences_dir = Path(__file__).parent.parent.parent / "data" / "command_sequences"
        self.sequences_dir.mkdir(exist_ok=True, parents=True)
        
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
        
        # Default wake words
        self.wake_words = {"hey tessa", "ok tessa", "hello tessa", "tessa"}
        self.wake_word_sensitivities = {
            "default": 0.7,  # Default sensitivity (0-1)
            "hey tessa": 0.65,
            "ok tessa": 0.65,
            "hello tessa": 0.7,
            "tessa": 0.8  # Higher sensitivity needed for single word
        }
        
        # Available languages for voice recognition and synthesis
        self.available_languages = {
            "en": {"name": "English", "tlds": ["com", "co.uk", "com.au", "ca", "co.in", "ie", "co.za"]},
            "es": {"name": "Spanish", "tlds": ["com", "es"]},
            "fr": {"name": "French", "tlds": ["com", "fr", "ca"]},
            "de": {"name": "German", "tlds": ["com", "de"]},
            "it": {"name": "Italian", "tlds": ["com", "it"]},
            "ja": {"name": "Japanese", "tlds": ["com", "co.jp"]},
            "ko": {"name": "Korean", "tlds": ["com"]},
            "pt": {"name": "Portuguese", "tlds": ["com", "com.br"]},
            "zh-CN": {"name": "Chinese (Simplified)", "tlds": ["com"]},
            "ru": {"name": "Russian", "tlds": ["com"]}
        }
        
        # Ambient mode settings
        self.ambient_mode_active = False
        self.ambient_mode_thread = None
        self.stop_ambient_mode = False
        self.wake_word_detected_callback = None
        self.ambient_mode_timeout = 300  # seconds before timing out if no wake word detected
        self.energy_threshold = 4000  # Default energy threshold for wake word detection
        self.dynamic_energy_adjustment = True  # Dynamically adjust for ambient noise
        self.use_offline_detection = False  # Whether to use offline wake word detection
        self.ambient_mode_pause_after_detection = 5  # Seconds to pause after wake word detected
        self.false_trigger_phrases = set(["okay google", "hey siri", "alexa", "hey cortana"])  # Phrases to ignore
        self.last_wake_word_time = None  # Time of last wake word detection
        self.wake_word_cooldown = 3  # Seconds to wait before detecting the same wake word again
        
        # Context for command sequences
        self.command_context = {}
        self.sequence_history = []
        self.active_sequence = None
        self.last_command_time = datetime.now()
        
        # Load or create profiles, shortcuts, and sequences
        self.profiles = self._load_profiles()
        self.voice_signatures = self._load_voice_signatures()
        self.shortcuts = self._load_shortcuts()
        self.sequences = self._load_sequences()
        
        self.active_profile_name = "tessa_default"
        self.active_user_id = None
        
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
                logger.error(f"Error loading profile {profile_file}: {e}")
                
        return profiles
    
    def _load_voice_signatures(self) -> Dict[str, VoiceSignature]:
        """Load voice signatures for authentication"""
        signatures = {}
        
        for sig_file in self.voice_auth_dir.glob("*.json"):
            try:
                with open(sig_file, "r") as f:
                    sig_data = json.load(f)
                    signature = VoiceSignature.from_dict(sig_data)
                    signatures[signature.user_id] = signature
            except Exception as e:
                logger.error(f"Error loading voice signature {sig_file}: {e}")
                
        return signatures
    
    def _load_shortcuts(self) -> Dict[str, VoiceShortcut]:
        """Load voice shortcuts from disk"""
        shortcuts = {}
        
        for shortcut_file in self.shortcuts_dir.glob("*.json"):
            try:
                with open(shortcut_file, "r") as f:
                    shortcut_data = json.load(f)
                    shortcut = VoiceShortcut.from_dict(shortcut_data)
                    shortcuts[shortcut_file.stem] = shortcut
            except Exception as e:
                logger.error(f"Error loading voice shortcut {shortcut_file}: {e}")
                
        return shortcuts
    
    def _load_sequences(self) -> Dict[str, CommandSequence]:
        """Load command sequences from disk"""
        sequences = {}
        
        for seq_file in self.sequences_dir.glob("*.json"):
            try:
                with open(seq_file, "r") as f:
                    seq_data = json.load(f)
                    sequence = CommandSequence.from_dict(seq_data)
                    sequences[seq_file.stem] = sequence
            except Exception as e:
                logger.error(f"Error loading command sequence {seq_file}: {e}")
                
        return sequences
        
    def save_profile(self, profile_name: str, profile: VoiceProfile):
        """Save a voice profile to disk"""
        profile_path = self.profiles_dir / f"{profile_name}.json"
        
        with open(profile_path, "w") as f:
            json.dump(profile.to_dict(), f, indent=2)
            
        # Update in-memory profiles
        self.profiles[profile_name] = profile
    
    def save_voice_signature(self, signature: VoiceSignature):
        """Save a user's voice signature for authentication"""
        sig_path = self.voice_auth_dir / f"{signature.user_id}.json"
        
        with open(sig_path, "w") as f:
            json.dump(signature.to_dict(), f, indent=2)
            
        # Update in-memory signatures
        self.voice_signatures[signature.user_id] = signature
    
    def save_shortcut(self, shortcut_id: str, shortcut: VoiceShortcut):
        """Save a voice shortcut to disk"""
        shortcut_path = self.shortcuts_dir / f"{shortcut_id}.json"
        
        with open(shortcut_path, "w") as f:
            json.dump(shortcut.to_dict(), f, indent=2)
            
        # Update in-memory shortcuts
        self.shortcuts[shortcut_id] = shortcut
    
    def save_sequence(self, sequence_id: str, sequence: CommandSequence):
        """Save a command sequence to disk"""
        sequence_path = self.sequences_dir / f"{sequence_id}.json"
        
        with open(sequence_path, "w") as f:
            json.dump(sequence.to_dict(), f, indent=2)
            
        # Update in-memory sequences
        self.sequences[sequence_id] = sequence
        
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
    
    def list_shortcuts(self, user_id: Optional[str] = None) -> List[VoiceShortcut]:
        """
        List all voice shortcuts
        
        Args:
            user_id: Optional user ID to filter shortcuts by user
            
        Returns:
            List of voice shortcuts
        """
        if user_id:
            return [s for s in self.shortcuts.values() if s.user_id is None or s.user_id == user_id]
        return list(self.shortcuts.values())
    
    def list_sequences(self, user_id: Optional[str] = None) -> List[CommandSequence]:
        """
        List all command sequences
        
        Args:
            user_id: Optional user ID to filter sequences by user
            
        Returns:
            List of command sequences
        """
        if user_id:
            return [s for s in self.sequences.values() if s.user_id is None or s.user_id == user_id]
        return list(self.sequences.values())
    
    def list_available_languages(self) -> Dict[str, Dict]:
        """List all available languages for voice recognition and synthesis"""
        return self.available_languages
    
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
    
    def extract_voice_features(self, audio_data_base64):
        """
        Extract voice features for authentication
        
        Args:
            audio_data_base64: Base64 encoded audio data
            
        Returns:
            numpy.ndarray: Voice features for authentication
        """
        try:
            # Decode base64 audio data
            audio_bytes = base64.b64decode(audio_data_base64.split(',')[1])
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
                temp_file.write(audio_bytes)
                temp_file_path = temp_file.name
            
            # Extract features
            y, sr = librosa.load(temp_file_path)
            
            # Clean up temporary file
            os.unlink(temp_file_path)
            
            # Extract MFCC features (common for voice authentication)
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=40)
            
            # Get statistical features
            mfccs_mean = np.mean(mfccs, axis=1)
            mfccs_var = np.var(mfccs, axis=1)
            
            # Combine features
            features = np.concatenate((mfccs_mean, mfccs_var))
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting voice features: {e}")
            return None
    
    def register_voice(self, user_id: str, audio_samples: List[str]) -> bool:
        """
        Register a user's voice for authentication
        
        Args:
            user_id: User ID
            audio_samples: List of base64 encoded audio samples
            
        Returns:
            bool: True if registration successful, False otherwise
        """
        try:
            features = []
            
            # Extract features from each audio sample
            for sample in audio_samples:
                feature = self.extract_voice_features(sample)
                if feature is not None:
                    features.append(feature)
            
            if len(features) < 3:
                logger.error(f"Insufficient valid voice samples for user {user_id}")
                return False
            
            # Create voice signature
            now = datetime.now().isoformat()
            signature = VoiceSignature(
                user_id=user_id,
                features=features,
                created_at=now,
                updated_at=now
            )
            
            # Save voice signature
            self.save_voice_signature(signature)
            
            return True
            
        except Exception as e:
            logger.error(f"Error registering voice for user {user_id}: {e}")
            return False
    
    def authenticate_voice(self, audio_data_base64: str, threshold: float = 0.7) -> Optional[str]:
        """
        Authenticate a user by their voice
        
        Args:
            audio_data_base64: Base64 encoded audio data
            threshold: Similarity threshold for authentication (0-1)
            
        Returns:
            str: User ID if authenticated, None otherwise
        """
        try:
            if not self.voice_signatures:
                logger.warning("No voice signatures registered for authentication")
                return None
            
            # Extract features from audio sample
            features = self.extract_voice_features(audio_data_base64)
            if features is None:
                return None
            
            best_match = None
            best_score = 0
            
            # Compare with registered voice signatures
            for user_id, signature in self.voice_signatures.items():
                scores = []
                
                # Calculate similarity with each registered sample
                for ref_features in signature.features:
                    # Calculate cosine similarity
                    similarity = np.dot(features, ref_features) / (np.linalg.norm(features) * np.linalg.norm(ref_features))
                    scores.append(similarity)
                
                # Get average similarity score
                avg_score = np.mean(scores)
                
                # Update best match
                if avg_score > best_score:
                    best_score = avg_score
                    best_match = user_id
            
            # Check if score exceeds threshold
            if best_score >= threshold:
                self.active_user_id = best_match
                logger.info(f"User {best_match} authenticated with score {best_score:.2f}")
                return best_match
            else:
                logger.warning(f"Voice authentication failed. Best match: {best_match} with score {best_score:.2f}")
                return None
            
        except Exception as e:
            logger.error(f"Error authenticating voice: {e}")
            return None
    
    def start_ambient_mode(self, callback=None, energy_threshold=None, use_offline=None):
        """
        Start ambient mode to listen for wake words
        
        Args:
            callback: Function to call when wake word is detected
            energy_threshold: Custom energy threshold for detection sensitivity
            use_offline: Whether to use offline wake word detection
            
        Returns:
            bool: True if ambient mode started successfully, False otherwise
        """
        if self.ambient_mode_active:
            logger.warning("Ambient mode already active")
            return False
        
        self.wake_word_detected_callback = callback
        self.stop_ambient_mode = False
        
        # Apply custom settings if provided
        if energy_threshold is not None:
            self.energy_threshold = energy_threshold
            
        if use_offline is not None:
            self.use_offline_detection = use_offline
        
        # Start ambient mode in a background thread
        self.ambient_mode_thread = threading.Thread(target=self._ambient_mode_listener, daemon=True)
        self.ambient_mode_thread.start()
        self.ambient_mode_active = True
        
        logger.info(f"Ambient mode started (Energy threshold: {self.energy_threshold}, Offline: {self.use_offline_detection})")
        return True
    
    def stop_ambient_mode(self):
        """Stop ambient mode"""
        if not self.ambient_mode_active:
            logger.warning("Ambient mode not active")
            return False
        
        self.stop_ambient_mode = True
        if self.ambient_mode_thread:
            self.ambient_mode_thread.join(timeout=2)
        
        self.ambient_mode_active = False
        logger.info("Ambient mode stopped")
        return True
    
    def _ambient_mode_listener(self):
        """Background thread for ambient mode listening"""
        logger.info("Ambient mode listener started")
        
        recognizer = sr.Recognizer()
        recognizer.energy_threshold = self.energy_threshold
        recognizer.dynamic_energy_threshold = self.dynamic_energy_adjustment
        
        # Adjust for ambient noise for better wake word detection
        try:
            with sr.Microphone() as source:
                logger.info("Adjusting for ambient noise...")
                recognizer.adjust_for_ambient_noise(source, duration=2)
                logger.info(f"Ambient noise adjustment complete. Energy threshold: {recognizer.energy_threshold}")
                # Store the adjusted threshold for future reference
                self.energy_threshold = recognizer.energy_threshold
        except Exception as e:
            logger.error(f"Error adjusting for ambient noise: {e}")
        
        start_time = datetime.now()
        continuous_silence_start = datetime.now()
        
        while not self.stop_ambient_mode:
            # Check if we've been listening too long without activity
            if (datetime.now() - start_time).total_seconds() > self.ambient_mode_timeout:
                logger.info(f"Ambient mode timed out after {self.ambient_mode_timeout} seconds")
                self.stop_ambient_mode = True
                break
            
            # Check if we've been in continuous silence for too long (power saving)
            if (datetime.now() - continuous_silence_start).total_seconds() > 60:
                # Increase check interval when no activity detected
                logger.debug("Entering power saving mode due to prolonged silence")
                time.sleep(0.5)  # Sleep longer in quiet environments
            
            try:
                with sr.Microphone() as source:
                    logger.debug("Listening for wake word...")
                    try:
                        # Use a shorter timeout to enable more responsive detection
                        audio = recognizer.listen(source, timeout=1, phrase_time_limit=4)
                        # Reset the continuous silence timer when sound is detected
                        continuous_silence_start = datetime.now()
                        
                        if self.use_offline_detection:
                            # Offline wake word detection using local model
                            detected_word = self._detect_wake_word_offline(audio)
                            if detected_word:
                                self._handle_wake_word_detection(detected_word, audio)
                        else:
                            # Online detection using speech recognition service
                            try:
                                text = recognizer.recognize_google(audio).lower()
                                logger.debug(f"Heard: {text}")
                                
                                # Ignore known false triggers for other assistants
                                if any(phrase in text for phrase in self.false_trigger_phrases):
                                    logger.debug(f"Ignored false trigger phrase in: {text}")
                                    continue
                                
                                # Check if wake word detected
                                for wake_word in self.wake_words:
                                    # Skip wake word detection if we're in cooldown period for this word
                                    if self.last_wake_word_time and wake_word == self.last_wake_word_time.get('word'):
                                        time_since_last = (datetime.now() - self.last_wake_word_time.get('time')).total_seconds()
                                        if time_since_last < self.wake_word_cooldown:
                                            continue
                                    
                                    sensitivity = self.wake_word_sensitivities.get(wake_word, 
                                                                                self.wake_word_sensitivities["default"])
                                    
                                    # Use phonetic matching for more natural detection
                                    if self._phonetic_match(wake_word, text, sensitivity):
                                        self._handle_wake_word_detection(wake_word, audio)
                                        break
                                        
                            except sr.UnknownValueError:
                                # Speech not recognized, continue listening
                                pass
                            except sr.RequestError:
                                logger.error("Could not request results from speech recognition service")
                                # If online services fail, attempt to use offline detection as fallback
                                if not self.use_offline_detection:
                                    detected_word = self._detect_wake_word_offline(audio)
                                    if detected_word:
                                        self._handle_wake_word_detection(detected_word, audio)
                                time.sleep(1)  # Wait before retrying
                    except sr.WaitTimeoutError:
                        pass  # No speech detected, continue listening
                        
            except Exception as e:
                logger.error(f"Error in ambient mode listener: {e}")
                time.sleep(1)
        
        logger.info("Ambient mode listener stopped")
    
    def _handle_wake_word_detection(self, wake_word, audio):
        """
        Handle wake word detection with common logic
        
        Args:
            wake_word: Detected wake word
            audio: Audio data containing the wake word
        """
        logger.info(f"Wake word detected: {wake_word}")
        
        # Record last detection time for cooldown
        self.last_wake_word_time = {
            'word': wake_word,
            'time': datetime.now()
        }
        
        # Call callback if provided
        if self.wake_word_detected_callback:
            audio_data = base64.b64encode(audio.get_wav_data()).decode('utf-8')
            self.wake_word_detected_callback(f"data:audio/wav;base64,{audio_data}")
        
        # Pause briefly after detection to avoid duplicate triggers
        time.sleep(self.ambient_mode_pause_after_detection)
    
    def _detect_wake_word_offline(self, audio):
        """
        Perform offline wake word detection using local processing
        
        Args:
            audio: Audio data to process
            
        Returns:
            str: Detected wake word or None
        """
        try:
            # Simplified offline detection using audio energy and duration analysis
            # This would be replaced with a proper wake word detection model in production
            audio_data = np.frombuffer(audio.get_raw_data(), np.int16)
            
            # Calculate audio energy
            audio_energy = np.sqrt(np.mean(np.square(audio_data)))
            
            # Simple threshold-based detection (placeholder for actual model)
            if audio_energy > self.energy_threshold * 1.5:
                logger.debug(f"High energy audio detected: {audio_energy}")
                
                # Return the first wake word as a fallback
                # In a real implementation, this would use an actual wake word detection model
                return list(self.wake_words)[0] if self.wake_words else None
                
            return None
        except Exception as e:
            logger.error(f"Error in offline wake word detection: {e}")
            return None
    
    def _phonetic_match(self, wake_word, text, sensitivity=0.7):
        """
        Match wake word using phonetic similarity for more natural detection
        
        Args:
            wake_word: Wake word to match
            text: Text to check against
            sensitivity: Match sensitivity (0-1)
            
        Returns:
            bool: True if wake word phonetically matches
        """
        # Simple containment check with adjustable sensitivity
        if wake_word in text:
            return True
            
        # Check for partial matches with longer wake phrases
        if len(wake_word.split()) > 1:
            wake_parts = wake_word.split()
            matched_parts = 0
            
            for part in wake_parts:
                if part in text:
                    matched_parts += 1
            
            # Calculate match percentage
            match_percent = matched_parts / len(wake_parts)
            if match_percent >= sensitivity:
                return True
        
        # TODO: Add more sophisticated phonetic matching algorithms
        # such as Soundex, Levenshtein distance, or machine learning model
        
        return False
    
    def add_wake_word(self, wake_word: str, sensitivity: float = 0.7):
        """
        Add a new wake word
        
        Args:
            wake_word: Wake word or phrase
            sensitivity: Detection sensitivity (0-1)
        
        Returns:
            bool: True if wake word added successfully
        """
        wake_word = wake_word.lower().strip()
        if wake_word:
            # Don't add wake words that might trigger other assistants
            if any(phrase in wake_word for phrase in self.false_trigger_phrases):
                logger.warning(f"Rejected wake word that could conflict with other assistants: {wake_word}")
                return False
                
            self.wake_words.add(wake_word)
            self.wake_word_sensitivities[wake_word] = sensitivity
            logger.info(f"Added wake word: '{wake_word}' with sensitivity {sensitivity}")
            return True
        return False
        
    def set_ambient_params(self, energy_threshold=None, dynamic_adjustment=None, 
                          offline_detection=None, pause_after_detection=None):
        """
        Configure ambient mode parameters
        
        Args:
            energy_threshold: Energy threshold for wake word detection
            dynamic_adjustment: Whether to dynamically adjust for ambient noise
            offline_detection: Whether to use offline wake word detection
            pause_after_detection: Seconds to pause after wake word detected
            
        Returns:
            dict: Current ambient mode parameters
        """
        if energy_threshold is not None:
            self.energy_threshold = energy_threshold
            
        if dynamic_adjustment is not None:
            self.dynamic_energy_adjustment = dynamic_adjustment
            
        if offline_detection is not None:
            self.use_offline_detection = offline_detection
            
        if pause_after_detection is not None:
            self.ambient_mode_pause_after_detection = pause_after_detection
        
        return {
            'energy_threshold': self.energy_threshold,
            'dynamic_adjustment': self.dynamic_energy_adjustment,
            'offline_detection': self.use_offline_detection,
            'pause_after_detection': self.ambient_mode_pause_after_detection,
            'active': self.ambient_mode_active
        }
    
    def remove_wake_word(self, wake_word: str):
        """
        Remove a wake word
        
        Args:
            wake_word: Wake word or phrase to remove
        
        Returns:
            bool: True if wake word removed successfully
        """
        wake_word = wake_word.lower().strip()
        if wake_word in self.wake_words:
            self.wake_words.remove(wake_word)
            if wake_word in self.wake_word_sensitivities:
                del self.wake_word_sensitivities[wake_word]
            return True
        return False
    
    def create_voice_shortcut(self, phrase: str, command: str, description: str, user_id: Optional[str] = None) -> str:
        """
        Create a new voice shortcut
        
        Args:
            phrase: Trigger phrase
            command: Command to execute
            description: Description of the shortcut
            user_id: Optional user ID to restrict shortcut to specific user
        
        Returns:
            str: Shortcut ID
        """
        shortcut_id = f"shortcut_{int(time.time())}"
        shortcut = VoiceShortcut(
            phrase=phrase.lower().strip(),
            command=command,
            description=description,
            user_id=user_id
        )
        
        self.save_shortcut(shortcut_id, shortcut)
        logger.info(f"Voice shortcut created: {shortcut_id}")
        return shortcut_id
    
    def delete_voice_shortcut(self, shortcut_id: str) -> bool:
        """
        Delete a voice shortcut
        
        Args:
            shortcut_id: Shortcut ID
        
        Returns:
            bool: True if shortcut deleted successfully
        """
        if shortcut_id in self.shortcuts:
            shortcut_path = self.shortcuts_dir / f"{shortcut_id}.json"
            if shortcut_path.exists():
                shortcut_path.unlink()
            
            del self.shortcuts[shortcut_id]
            logger.info(f"Voice shortcut deleted: {shortcut_id}")
            return True
        
        logger.warning(f"Voice shortcut not found: {shortcut_id}")
        return False
    
    def match_voice_shortcut(self, text: str, user_id: Optional[str] = None) -> Optional[VoiceShortcut]:
        """
        Match text against voice shortcuts
        
        Args:
            text: Input text
            user_id: Optional user ID to filter shortcuts
        
        Returns:
            VoiceShortcut: Matching shortcut or None
        """
        text = text.lower().strip()
        
        # Get shortcuts for this user or global shortcuts
        available_shortcuts = [
            s for s in self.shortcuts.values() 
            if s.user_id is None or (user_id and s.user_id == user_id)
        ]
        
        # Find matching shortcut
        for shortcut in available_shortcuts:
            if shortcut.phrase in text:
                return shortcut
        
        return None
    
    def create_command_sequence(self, name: str, triggers: List[str], steps: List[str], 
                               context_requirements: Dict[str, str] = None, 
                               user_id: Optional[str] = None) -> str:
        """
        Create a new command sequence
        
        Args:
            name: Sequence name
            triggers: List of trigger phrases
            steps: List of command steps
            context_requirements: Optional context requirements
            user_id: Optional user ID to restrict sequence to specific user
        
        Returns:
            str: Sequence ID
        """
        sequence_id = f"sequence_{int(time.time())}"
        sequence = CommandSequence(
            name=name,
            triggers=[t.lower().strip() for t in triggers],
            steps=steps,
            context_requirements=context_requirements or {},
            user_id=user_id
        )
        
        self.save_sequence(sequence_id, sequence)
        logger.info(f"Command sequence created: {sequence_id}")
        return sequence_id
    
    def delete_command_sequence(self, sequence_id: str) -> bool:
        """
        Delete a command sequence
        
        Args:
            sequence_id: Sequence ID
        
        Returns:
            bool: True if sequence deleted successfully
        """
        if sequence_id in self.sequences:
            sequence_path = self.sequences_dir / f"{sequence_id}.json"
            if sequence_path.exists():
                sequence_path.unlink()
            
            del self.sequences[sequence_id]
            logger.info(f"Command sequence deleted: {sequence_id}")
            return True
        
        logger.warning(f"Command sequence not found: {sequence_id}")
        return False
    
    def match_command_sequence(self, text: str, context: Dict[str, str], user_id: Optional[str] = None) -> Optional[CommandSequence]:
        """
        Match text against command sequences
        
        Args:
            text: Input text
            context: Current context
            user_id: Optional user ID to filter sequences
        
        Returns:
            CommandSequence: Matching sequence or None
        """
        text = text.lower().strip()
        
        # Get sequences for this user or global sequences
        available_sequences = [
            s for s in self.sequences.values() 
            if s.user_id is None or (user_id and s.user_id == user_id)
        ]
        
        # Find matching sequence
        for sequence in available_sequences:
            # Check if trigger matches
            if any(trigger in text for trigger in sequence.triggers):
                # Check if context requirements are met
                context_match = True
                for key, value in sequence.context_requirements.items():
                    if key not in context or context[key] != value:
                        context_match = False
                        break
                
                if context_match:
                    return sequence
        
        return None
    
    def update_command_context(self, context_updates: Dict[str, str]):
        """
        Update command context
        
        Args:
            context_updates: Context updates
        """
        self.command_context.update(context_updates)
        self.last_command_time = datetime.now()
    
    def clear_command_context(self):
        """Clear command context"""
        self.command_context = {}
        self.active_sequence = None
    
    def get_next_sequence_step(self) -> Optional[str]:
        """
        Get the next step in the active sequence
        
        Returns:
            str: Next command step or None if sequence is complete
        """
        if not self.active_sequence:
            return None
        
        # Check if sequence has expired (no activity for 5 minutes)
        if (datetime.now() - self.last_command_time) > timedelta(minutes=5):
            logger.info("Command sequence expired due to inactivity")
            self.active_sequence = None
            return None
        
        # Get sequence and current position
        sequence = self.sequences.get(self.active_sequence["id"])
        if not sequence:
            self.active_sequence = None
            return None
        
        position = self.active_sequence["position"]
        
        # Check if sequence is complete
        if position >= len(sequence.steps):
            logger.info(f"Command sequence {self.active_sequence['id']} completed")
            self.active_sequence = None
            return None
        
        # Get next step and increment position
        next_step = sequence.steps[position]
        self.active_sequence["position"] += 1
        
        return next_step
    
    def start_sequence(self, sequence_id: str) -> bool:
        """
        Start a command sequence
        
        Args:
            sequence_id: Sequence ID
        
        Returns:
            bool: True if sequence started successfully
        """
        if sequence_id in self.sequences:
            self.active_sequence = {
                "id": sequence_id,
                "position": 0,
                "started_at": datetime.now().isoformat()
            }
            self.last_command_time = datetime.now()
            logger.info(f"Command sequence started: {sequence_id}")
            return True
        
        logger.warning(f"Command sequence not found: {sequence_id}")
        return False
        
    def speech_to_text(self, audio_data, language="en"):
        """
        Convert speech to text using Google Speech Recognition
        
        Args:
            audio_data: Base64 encoded audio data in WAV format
            language: Language code for speech recognition
        
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
            text = self.recognizer.recognize_google(audio, language=language)
            
            # Check for voice authentication request
            if text.lower().strip() in ["authenticate me", "authenticate voice", "voice login"]:
                user_id = self.authenticate_voice(audio_data)
                if user_id:
                    return {'success': True, 'text': text, 'authenticated': True, 'user_id': user_id}
                else:
                    return {'success': True, 'text': text, 'authenticated': False}
            
            # Check for shortcuts if user is authenticated
            if self.active_user_id:
                shortcut = self.match_voice_shortcut(text, self.active_user_id)
                if shortcut:
                    return {'success': True, 'text': text, 'shortcut': shortcut.to_dict()}
            
            # Check for wake words in ambient mode
            for wake_word in self.wake_words:
                if wake_word in text.lower():
                    return {'success': True, 'text': text, 'wake_word': wake_word}
            
            return {'success': True, 'text': text}
            
        except sr.UnknownValueError:
            return {'success': False, 'error': 'Could not understand audio'}
        except sr.RequestError as e:
            return {'success': False, 'error': f'Error with the speech recognition service: {str(e)}'}
        except Exception as e:
            return {'success': False, 'error': f'Error processing audio: {str(e)}'}

    def text_to_speech(self, text, add_personality=True, language=None):
        """
        Convert text to speech using Google Text-to-Speech
        with customizable voice profile
        
        Args:
            text: Text to convert to speech
            add_personality: Whether to add personality quirks
            language: Override language (uses profile language if None)
            
        Returns:
            dict: Contains base64 encoded audio data or error message
        """
        try:
            # Apply personality if enabled
            if add_personality:
                text = self.add_personality(text)
                
            # Get active profile
            profile = self.get_active_profile()
            
            # Use specified language or profile language
            lang = language or profile.lang
            
            # Get appropriate TLD for language
            available_tlds = self.available_languages.get(lang, {}).get("tlds", ["com"])
            tld = profile.tld if profile.tld in available_tlds else available_tlds[0]
            
            # Create a temporary file for the audio
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                # Generate speech with profile settings
                tts = gTTS(
                    text=text, 
                    lang=lang, 
                    tld=tld,
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
                    'profile': profile.name,
                    'language': lang
                }
                
        except Exception as e:
            logger.error(f"Error generating speech: {e}")
            return {'success': False, 'error': f'Error generating speech: {str(e)}'}