# voice_handler

Voice handler module for speech recognition and synthesis with personalized voice profiles.
Includes voice authentication, wake word detection, and multi-language support.

**Module Path**: `proxmox_nli.core.voice_handler`

## Classes

### VoiceProfile

Voice profile settings for TTS customization

#### to_dict()

Convert profile to dictionary

#### from_dict(cls, data)

Create profile from dictionary

### VoiceShortcut

Custom voice shortcut for quick command execution

#### to_dict()

Convert shortcut to dictionary

#### from_dict(cls, data)

Create shortcut from dictionary

### CommandSequence

Context-aware command sequence definition

#### to_dict()

Convert command sequence to dictionary

#### from_dict(cls, data)

Create command sequence from dictionary

### VoiceSignature

Voice fingerprint for user authentication

#### to_dict()

Convert voice signature to dictionary

#### from_dict(cls, data)

Create voice signature from dictionary

### VoiceHandler

#### __init__()

Initialize the voice handler

#### save_profile(profile_name: str, profile: VoiceProfile)

Save a voice profile to disk

#### save_voice_signature(signature: VoiceSignature)

Save a user's voice signature for authentication

#### save_shortcut(shortcut_id: str, shortcut: VoiceShortcut)

Save a voice shortcut to disk

#### save_sequence(sequence_id: str, sequence: CommandSequence)

Save a command sequence to disk

#### set_active_profile(profile_name: str)

Set the active voice profile

#### get_active_profile()

Get the current active voice profile

**Returns**: `VoiceProfile`

#### list_profiles()

List all available voice profiles

**Returns**: `List[str]`

#### list_shortcuts(user_id: Optional[str])

List all voice shortcuts

Args:
    user_id: Optional user ID to filter shortcuts by user
    
Returns:
    List of voice shortcuts

**Returns**: `List[VoiceShortcut]`

#### list_sequences(user_id: Optional[str])

List all command sequences

Args:
    user_id: Optional user ID to filter sequences by user
    
Returns:
    List of command sequences

**Returns**: `List[CommandSequence]`

#### list_available_languages()

List all available languages for voice recognition and synthesis

**Returns**: `Dict[(str, Dict)]`

#### adapt_to_user_experience(experience_level: float)

Adapt TESSA's voice to user experience level

Args:
    experience_level: Float from 0.0 (beginner) to 1.0 (expert)

#### add_personality(text: str, probability: float)

Add personality quirks to responses

Args:
    text: The text to potentially modify
    probability: Chance (0-1) of adding a personality phrase
    
Returns:
    str: Text with personality additions

**Returns**: `str`

#### extract_voice_features(audio_data_base64)

Extract voice features for authentication

Args:
    audio_data_base64: Base64 encoded audio data
    
Returns:
    numpy.ndarray: Voice features for authentication

**Returns**: `numpy.ndarray: Voice features for authentication`

#### register_voice(user_id: str, audio_samples: List[str])

Register a user's voice for authentication

Args:
    user_id: User ID
    audio_samples: List of base64 encoded audio samples
    
Returns:
    bool: True if registration successful, False otherwise

**Returns**: `bool`

#### authenticate_voice(audio_data_base64: str, threshold: float)

Authenticate a user by their voice

Args:
    audio_data_base64: Base64 encoded audio data
    threshold: Similarity threshold for authentication (0-1)
    
Returns:
    str: User ID if authenticated, None otherwise

**Returns**: `Optional[str]`

#### start_ambient_mode(callback)

Start ambient mode to listen for wake words

Args:
    callback: Function to call when wake word is detected

Returns:
    bool: True if ambient mode started successfully, False otherwise

**Returns**: `bool: True if ambient mode started successfully, False otherwise`

#### stop_ambient_mode()

Stop ambient mode

#### add_wake_word(wake_word: str, sensitivity: float)

Add a new wake word

Args:
    wake_word: Wake word or phrase
    sensitivity: Detection sensitivity (0-1)

Returns:
    bool: True if wake word added successfully

**Returns**: `bool: True if wake word added successfully`

#### remove_wake_word(wake_word: str)

Remove a wake word

Args:
    wake_word: Wake word or phrase to remove

Returns:
    bool: True if wake word removed successfully

**Returns**: `bool: True if wake word removed successfully`

#### create_voice_shortcut(phrase: str, command: str, description: str, user_id: Optional[str])

Create a new voice shortcut

Args:
    phrase: Trigger phrase
    command: Command to execute
    description: Description of the shortcut
    user_id: Optional user ID to restrict shortcut to specific user

Returns:
    str: Shortcut ID

**Returns**: `str`

#### delete_voice_shortcut(shortcut_id: str)

Delete a voice shortcut

Args:
    shortcut_id: Shortcut ID

Returns:
    bool: True if shortcut deleted successfully

**Returns**: `bool`

#### match_voice_shortcut(text: str, user_id: Optional[str])

Match text against voice shortcuts

Args:
    text: Input text
    user_id: Optional user ID to filter shortcuts

Returns:
    VoiceShortcut: Matching shortcut or None

**Returns**: `Optional[VoiceShortcut]`

#### create_command_sequence(name: str, triggers: List[str], steps: List[str], context_requirements: Dict[(str, str)], user_id: Optional[str] = None)

Create a new command sequence

Args:
    name: Sequence name
    triggers: List of trigger phrases
    steps: List of command steps
    context_requirements: Optional context requirements
    user_id: Optional user ID to restrict sequence to specific user

Returns:
    str: Sequence ID

**Returns**: `str`

#### delete_command_sequence(sequence_id: str)

Delete a command sequence

Args:
    sequence_id: Sequence ID

Returns:
    bool: True if sequence deleted successfully

**Returns**: `bool`

#### match_command_sequence(text: str, context: Dict[(str, str)], user_id: Optional[str])

Match text against command sequences

Args:
    text: Input text
    context: Current context
    user_id: Optional user ID to filter sequences

Returns:
    CommandSequence: Matching sequence or None

**Returns**: `Optional[CommandSequence]`

#### update_command_context(context_updates: Dict[(str, str)])

Update command context

Args:
    context_updates: Context updates

#### clear_command_context()

Clear command context

#### get_next_sequence_step()

Get the next step in the active sequence

Returns:
    str: Next command step or None if sequence is complete

**Returns**: `Optional[str]`

#### start_sequence(sequence_id: str)

Start a command sequence

Args:
    sequence_id: Sequence ID

Returns:
    bool: True if sequence started successfully

**Returns**: `bool`

#### speech_to_text(audio_data, language)

Convert speech to text using Google Speech Recognition

Args:
    audio_data: Base64 encoded audio data in WAV format
    language: Language code for speech recognition

Returns:
    dict: Contains recognized text or error message

**Returns**: `dict: Contains recognized text or error message`

#### text_to_speech(text, add_personality, language = True)

Convert text to speech using Google Text-to-Speech
with customizable voice profile

Args:
    text: Text to convert to speech
    add_personality: Whether to add personality quirks
    language: Override language (uses profile language if None)
    
Returns:
    dict: Contains base64 encoded audio data or error message

**Returns**: `dict: Contains base64 encoded audio data or error message`

