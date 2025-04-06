"""
TESSA Personality Growth Module.

This module enables TESSA to adapt and evolve its personality based on
household usage patterns and user interactions.
"""
import logging
import json
import os
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import threading
import random

import numpy as np
from sklearn.cluster import KMeans

logger = logging.getLogger(__name__)

class TessaPersonality:
    """Manages TESSA's personality growth and adaptation."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize TESSA's personality system.
        
        Args:
            config_path: Optional path to personality configuration file
        """
        self.config_path = config_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'config', 'tessa_personality.json'
        )
        
        # Default personality traits
        self.default_traits = {
            'helpfulness': 0.8,
            'formality': 0.5,
            'humor': 0.3,
            'verbosity': 0.5,
            'proactivity': 0.6,
            'technical_detail': 0.7
        }
        
        # Load or initialize personality data
        self.personality = self._load_personality()
        
        # Interaction history
        self.interactions = []
        self.max_interactions = 1000  # Maximum interactions to store
        
        # Usage patterns
        self.usage_patterns = {
            'time_of_day': {},
            'command_categories': {},
            'user_preferences': {},
            'household_activity': {}
        }
        
        # Growth parameters
        self.growth_rate = 0.01  # Rate of personality change
        self.adaptation_threshold = 10  # Minimum interactions before adaptation
        
        # Runtime state
        self.running = False
        self.monitor_thread = None
    
    def _load_personality(self) -> Dict[str, Any]:
        """Load personality from file or initialize with defaults."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    personality = json.load(f)
                logger.info("Loaded TESSA personality from file")
                return personality
            else:
                # Initialize with defaults
                personality = {
                    'traits': self.default_traits.copy(),
                    'learned_preferences': {},
                    'adaptation_level': 0,
                    'creation_date': datetime.now().isoformat(),
                    'last_updated': datetime.now().isoformat()
                }
                self._save_personality(personality)
                logger.info("Initialized new TESSA personality")
                return personality
        except Exception as e:
            logger.error(f"Error loading personality: {str(e)}")
            # Fall back to defaults
            return {
                'traits': self.default_traits.copy(),
                'learned_preferences': {},
                'adaptation_level': 0,
                'creation_date': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat()
            }
    
    def _save_personality(self, personality: Dict[str, Any] = None) -> bool:
        """Save personality to file."""
        try:
            personality = personality or self.personality
            personality['last_updated'] = datetime.now().isoformat()
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            with open(self.config_path, 'w') as f:
                json.dump(personality, f, indent=2)
            
            logger.info("Saved TESSA personality to file")
            return True
        except Exception as e:
            logger.error(f"Error saving personality: {str(e)}")
            return False
    
    def start_adaptation(self) -> Dict[str, Any]:
        """Start the personality adaptation process."""
        try:
            if self.running:
                return {
                    "success": False,
                    "message": "Personality adaptation is already running"
                }
            
            self.running = True
            self.monitor_thread = threading.Thread(
                target=self._adaptation_loop,
                daemon=True
            )
            self.monitor_thread.start()
            
            logger.info("TESSA personality adaptation started")
            return {
                "success": True,
                "message": "Personality adaptation started successfully"
            }
        except Exception as e:
            logger.error(f"Error starting personality adaptation: {str(e)}")
            return {
                "success": False,
                "message": f"Error starting personality adaptation: {str(e)}"
            }
    
    def stop_adaptation(self) -> Dict[str, Any]:
        """Stop the personality adaptation process."""
        try:
            if not self.running:
                return {
                    "success": False,
                    "message": "Personality adaptation is not running"
                }
            
            self.running = False
            if self.monitor_thread:
                self.monitor_thread.join(timeout=5)
            
            logger.info("TESSA personality adaptation stopped")
            return {
                "success": True,
                "message": "Personality adaptation stopped successfully"
            }
        except Exception as e:
            logger.error(f"Error stopping personality adaptation: {str(e)}")
            return {
                "success": False,
                "message": f"Error stopping personality adaptation: {str(e)}"
            }
    
    def get_personality(self) -> Dict[str, Any]:
        """Get current personality traits and adaptation level."""
        return {
            "success": True,
            "personality": {
                "traits": self.personality['traits'],
                "adaptation_level": self.personality['adaptation_level'],
                "creation_date": self.personality['creation_date'],
                "age_days": (datetime.now() - datetime.fromisoformat(self.personality['creation_date'])).days
            }
        }
    
    def reset_personality(self) -> Dict[str, Any]:
        """Reset personality to default values."""
        try:
            self.personality['traits'] = self.default_traits.copy()
            self.personality['learned_preferences'] = {}
            self.personality['adaptation_level'] = 0
            self._save_personality()
            
            return {
                "success": True,
                "message": "Personality reset to defaults",
                "personality": self.personality['traits']
            }
        except Exception as e:
            logger.error(f"Error resetting personality: {str(e)}")
            return {
                "success": False,
                "message": f"Error resetting personality: {str(e)}"
            }
    
    def record_interaction(self, interaction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Record a user interaction for personality adaptation.
        
        Args:
            interaction: Dict with interaction details
                - type: Type of interaction (command, conversation, etc.)
                - content: Content of the interaction
                - user: User identifier
                - timestamp: Interaction timestamp (optional)
                - metadata: Additional metadata (optional)
                
        Returns:
            Dict with operation result
        """
        try:
            # Add timestamp if not provided
            if 'timestamp' not in interaction:
                interaction['timestamp'] = datetime.now().isoformat()
            
            # Add to interactions list
            self.interactions.append(interaction)
            
            # Trim if exceeding max size
            if len(self.interactions) > self.max_interactions:
                self.interactions = self.interactions[-self.max_interactions:]
            
            # Update usage patterns
            self._update_usage_patterns(interaction)
            
            # Trigger adaptation if threshold reached
            if len(self.interactions) >= self.adaptation_threshold:
                self._adapt_personality()
            
            return {
                "success": True,
                "message": "Interaction recorded"
            }
        except Exception as e:
            logger.error(f"Error recording interaction: {str(e)}")
            return {
                "success": False,
                "message": f"Error recording interaction: {str(e)}"
            }
    
    def get_response_style(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Get the current response style based on personality and context.
        
        Args:
            context: Optional context for the response
                - user: User identifier
                - time: Current time
                - category: Command/conversation category
                - urgency: Urgency level
                
        Returns:
            Dict with response style parameters
        """
        try:
            # Start with base personality traits
            traits = self.personality['traits'].copy()
            
            # Adjust based on context if provided
            if context:
                # Adjust based on time of day
                if 'time' in context:
                    time_obj = datetime.fromisoformat(context['time']) if isinstance(context['time'], str) else context['time']
                    hour = time_obj.hour
                    
                    # More formal during business hours, more casual in evening
                    if 9 <= hour <= 17:
                        traits['formality'] = min(1.0, traits['formality'] + 0.1)
                    elif 20 <= hour or hour <= 5:
                        traits['formality'] = max(0.0, traits['formality'] - 0.1)
                        traits['humor'] = min(1.0, traits['humor'] + 0.1)
                
                # Adjust based on user preferences
                if 'user' in context and context['user'] in self.personality.get('learned_preferences', {}):
                    user_prefs = self.personality['learned_preferences'][context['user']]
                    for trait, value in user_prefs.items():
                        if trait in traits:
                            # Blend personality with user preference (70% personality, 30% user preference)
                            traits[trait] = traits[trait] * 0.7 + value * 0.3
                
                # Adjust based on urgency
                if 'urgency' in context:
                    urgency = float(context['urgency'])
                    if urgency > 0.7:
                        # More direct, less verbose for urgent matters
                        traits['verbosity'] = max(0.2, traits['verbosity'] - 0.2)
                        traits['humor'] = max(0.0, traits['humor'] - 0.2)
                        traits['technical_detail'] = max(0.3, traits['technical_detail'] - 0.1)
                
                # Adjust based on category
                if 'category' in context:
                    category = context['category']
                    if category == 'technical':
                        traits['technical_detail'] = min(1.0, traits['technical_detail'] + 0.1)
                    elif category == 'casual':
                        traits['formality'] = max(0.0, traits['formality'] - 0.2)
                        traits['humor'] = min(1.0, traits['humor'] + 0.2)
            
            # Generate concrete style parameters
            style = {
                "greeting_style": self._get_greeting_style(traits),
                "response_length": self._get_response_length(traits),
                "technical_level": self._get_technical_level(traits),
                "humor_level": self._get_humor_level(traits),
                "formality_level": self._get_formality_level(traits),
                "proactivity_level": self._get_proactivity_level(traits),
                "traits": traits
            }
            
            return {
                "success": True,
                "style": style
            }
        except Exception as e:
            logger.error(f"Error getting response style: {str(e)}")
            return {
                "success": False,
                "message": f"Error getting response style: {str(e)}",
                "style": {
                    "greeting_style": "neutral",
                    "response_length": "medium",
                    "technical_level": "medium",
                    "humor_level": "low",
                    "formality_level": "medium",
                    "proactivity_level": "medium"
                }
            }
    
    def _adaptation_loop(self):
        """Main loop for continuous personality adaptation."""
        adaptation_interval = 3600  # 1 hour
        
        while self.running:
            try:
                # Analyze recent interactions and adapt personality
                if self.interactions:
                    self._adapt_personality()
                
                # Save personality
                self._save_personality()
                
                # Sleep until next adaptation
                time.sleep(adaptation_interval)
            except Exception as e:
                logger.error(f"Error in personality adaptation loop: {str(e)}")
                time.sleep(60)  # Sleep for a minute before retrying
    
    def _update_usage_patterns(self, interaction: Dict[str, Any]):
        """Update usage pattern statistics based on new interaction."""
        try:
            # Extract timestamp
            timestamp = datetime.fromisoformat(interaction['timestamp']) if isinstance(interaction['timestamp'], str) else interaction['timestamp']
            
            # Update time of day patterns
            hour = timestamp.hour
            hour_key = f"{hour:02d}"
            if hour_key not in self.usage_patterns['time_of_day']:
                self.usage_patterns['time_of_day'][hour_key] = 0
            self.usage_patterns['time_of_day'][hour_key] += 1
            
            # Update command category patterns
            if 'category' in interaction:
                category = interaction['category']
                if category not in self.usage_patterns['command_categories']:
                    self.usage_patterns['command_categories'][category] = 0
                self.usage_patterns['command_categories'][category] += 1
            
            # Update user preferences
            if 'user' in interaction:
                user = interaction['user']
                if user not in self.usage_patterns['user_preferences']:
                    self.usage_patterns['user_preferences'][user] = {
                        'interactions': 0,
                        'categories': {},
                        'feedback': {},
                        'response_time': []
                    }
                
                self.usage_patterns['user_preferences'][user]['interactions'] += 1
                
                if 'category' in interaction:
                    category = interaction['category']
                    if category not in self.usage_patterns['user_preferences'][user]['categories']:
                        self.usage_patterns['user_preferences'][user]['categories'][category] = 0
                    self.usage_patterns['user_preferences'][user]['categories'][category] += 1
                
                if 'feedback' in interaction:
                    feedback = interaction['feedback']
                    if feedback not in self.usage_patterns['user_preferences'][user]['feedback']:
                        self.usage_patterns['user_preferences'][user]['feedback'][feedback] = 0
                    self.usage_patterns['user_preferences'][user]['feedback'][feedback] += 1
            
            # Update household activity
            day_of_week = timestamp.strftime('%A')
            hour_key = f"{hour:02d}"
            
            if day_of_week not in self.usage_patterns['household_activity']:
                self.usage_patterns['household_activity'][day_of_week] = {}
            
            if hour_key not in self.usage_patterns['household_activity'][day_of_week]:
                self.usage_patterns['household_activity'][day_of_week][hour_key] = 0
            
            self.usage_patterns['household_activity'][day_of_week][hour_key] += 1
        
        except Exception as e:
            logger.error(f"Error updating usage patterns: {str(e)}")
    
    def _adapt_personality(self):
        """Adapt personality based on usage patterns and interactions."""
        try:
            # Skip if not enough interactions
            if len(self.interactions) < self.adaptation_threshold:
                return
            
            # Get recent interactions
            recent = self.interactions[-self.adaptation_threshold:]
            
            # Extract features for adaptation
            features = self._extract_adaptation_features(recent)
            
            # Update traits based on features
            self._update_traits(features)
            
            # Update learned preferences
            self._update_learned_preferences(recent)
            
            # Increment adaptation level
            self.personality['adaptation_level'] += 1
            
            logger.info(f"Adapted personality to level {self.personality['adaptation_level']}")
        except Exception as e:
            logger.error(f"Error adapting personality: {str(e)}")
    
    def _extract_adaptation_features(self, interactions: List[Dict]) -> Dict[str, float]:
        """Extract features from interactions for personality adaptation."""
        features = {
            'formality_preference': 0.5,
            'verbosity_preference': 0.5,
            'technical_preference': 0.5,
            'humor_preference': 0.5,
            'proactivity_preference': 0.5,
            'active_hours': [],
            'command_complexity': 0.5
        }
        
        try:
            # Count interactions with feedback
            positive_feedback = 0
            negative_feedback = 0
            total_with_feedback = 0
            
            # Analyze each interaction
            for interaction in interactions:
                # Extract timestamp
                timestamp = datetime.fromisoformat(interaction['timestamp']) if isinstance(interaction['timestamp'], str) else interaction['timestamp']
                features['active_hours'].append(timestamp.hour)
                
                # Process feedback
                if 'feedback' in interaction:
                    feedback = interaction['feedback']
                    total_with_feedback += 1
                    
                    if feedback in ['positive', 'helpful', 'good']:
                        positive_feedback += 1
                        
                        # Extract traits that led to positive feedback
                        if 'response_style' in interaction:
                            style = interaction['response_style']
                            if 'formality_level' in style:
                                features['formality_preference'] += self._normalize_trait_value(style['formality_level'])
                            if 'verbosity_level' in style:
                                features['verbosity_preference'] += self._normalize_trait_value(style['verbosity_level'])
                            if 'technical_level' in style:
                                features['technical_preference'] += self._normalize_trait_value(style['technical_level'])
                            if 'humor_level' in style:
                                features['humor_preference'] += self._normalize_trait_value(style['humor_level'])
                            if 'proactivity_level' in style:
                                features['proactivity_preference'] += self._normalize_trait_value(style['proactivity_level'])
                    
                    elif feedback in ['negative', 'unhelpful', 'bad']:
                        negative_feedback += 1
                        
                        # Extract traits that led to negative feedback
                        if 'response_style' in interaction:
                            style = interaction['response_style']
                            if 'formality_level' in style:
                                features['formality_preference'] -= self._normalize_trait_value(style['formality_level'])
                            if 'verbosity_level' in style:
                                features['verbosity_preference'] -= self._normalize_trait_value(style['verbosity_level'])
                            if 'technical_level' in style:
                                features['technical_preference'] -= self._normalize_trait_value(style['technical_level'])
                            if 'humor_level' in style:
                                features['humor_preference'] -= self._normalize_trait_value(style['humor_level'])
                            if 'proactivity_level' in style:
                                features['proactivity_preference'] -= self._normalize_trait_value(style['proactivity_level'])
                
                # Analyze command complexity
                if 'type' in interaction and interaction['type'] == 'command':
                    if 'content' in interaction:
                        content = interaction['content']
                        # Simple heuristic for command complexity
                        words = content.split()
                        if len(words) > 10:
                            features['command_complexity'] += 0.1
                        elif len(words) < 5:
                            features['command_complexity'] -= 0.1
            
            # Normalize features
            if total_with_feedback > 0:
                features['formality_preference'] = self._clamp(features['formality_preference'] / total_with_feedback)
                features['verbosity_preference'] = self._clamp(features['verbosity_preference'] / total_with_feedback)
                features['technical_preference'] = self._clamp(features['technical_preference'] / total_with_feedback)
                features['humor_preference'] = self._clamp(features['humor_preference'] / total_with_feedback)
                features['proactivity_preference'] = self._clamp(features['proactivity_preference'] / total_with_feedback)
            
            features['command_complexity'] = self._clamp(features['command_complexity'])
            
            # Analyze active hours
            if features['active_hours']:
                # Cluster hours to find activity patterns
                hours_array = np.array(features['active_hours']).reshape(-1, 1)
                if len(hours_array) >= 3:  # Need at least 3 points for meaningful clustering
                    kmeans = KMeans(n_clusters=min(3, len(hours_array)), random_state=0).fit(hours_array)
                    centers = kmeans.cluster_centers_.flatten()
                    # Convert to list of peak hours
                    features['active_hours'] = [int(round(h)) % 24 for h in centers]
                else:
                    # Just use the average if not enough data
                    features['active_hours'] = [int(round(sum(features['active_hours']) / len(features['active_hours']))) % 24]
            
            return features
        
        except Exception as e:
            logger.error(f"Error extracting adaptation features: {str(e)}")
            return features
    
    def _update_traits(self, features: Dict[str, Any]):
        """Update personality traits based on extracted features."""
        try:
            traits = self.personality['traits']
            
            # Gradually adapt traits based on features
            traits['formality'] = self._adapt_trait(traits['formality'], features['formality_preference'])
            traits['verbosity'] = self._adapt_trait(traits['verbosity'], features['verbosity_preference'])
            traits['technical_detail'] = self._adapt_trait(traits['technical_detail'], features['technical_preference'])
            traits['humor'] = self._adapt_trait(traits['humor'], features['humor_preference'])
            traits['proactivity'] = self._adapt_trait(traits['proactivity'], features['proactivity_preference'])
            
            # Adjust helpfulness based on command complexity
            if features['command_complexity'] > 0.7:
                # More complex commands might need more helpful responses
                traits['helpfulness'] = self._adapt_trait(traits['helpfulness'], 0.9)
            
            # Ensure traits stay within bounds
            for trait in traits:
                traits[trait] = self._clamp(traits[trait])
        
        except Exception as e:
            logger.error(f"Error updating traits: {str(e)}")
    
    def _update_learned_preferences(self, interactions: List[Dict]):
        """Update learned user preferences based on interactions."""
        try:
            # Group interactions by user
            user_interactions = {}
            for interaction in interactions:
                if 'user' in interaction:
                    user = interaction['user']
                    if user not in user_interactions:
                        user_interactions[user] = []
                    user_interactions[user].append(interaction)
            
            # Process each user's interactions
            for user, user_ints in user_interactions.items():
                # Extract features for this user
                features = self._extract_adaptation_features(user_ints)
                
                # Initialize user preferences if needed
                if 'learned_preferences' not in self.personality:
                    self.personality['learned_preferences'] = {}
                
                if user not in self.personality['learned_preferences']:
                    self.personality['learned_preferences'][user] = {}
                
                # Update user preferences
                prefs = self.personality['learned_preferences'][user]
                prefs['formality'] = features['formality_preference']
                prefs['verbosity'] = features['verbosity_preference']
                prefs['technical_detail'] = features['technical_preference']
                prefs['humor'] = features['humor_preference']
                prefs['proactivity'] = features['proactivity_preference']
                prefs['active_hours'] = features['active_hours']
                prefs['last_updated'] = datetime.now().isoformat()
        
        except Exception as e:
            logger.error(f"Error updating learned preferences: {str(e)}")
    
    def _adapt_trait(self, current: float, target: float) -> float:
        """Gradually adapt a trait toward a target value."""
        if abs(current - target) < 0.05:
            return current  # No change needed
        
        # Move toward target at growth rate
        direction = 1 if target > current else -1
        return current + (direction * self.growth_rate)
    
    def _normalize_trait_value(self, value) -> float:
        """Normalize a trait value to a float between 0 and 1."""
        if isinstance(value, (int, float)):
            return self._clamp(value)
        elif isinstance(value, str):
            # Convert string values to float
            value_map = {
                'very_low': 0.0,
                'low': 0.25,
                'medium': 0.5,
                'high': 0.75,
                'very_high': 1.0
            }
            return value_map.get(value.lower(), 0.5)
        return 0.5
    
    def _clamp(self, value: float) -> float:
        """Clamp a value between 0 and 1."""
        return max(0.0, min(1.0, value))
    
    def _get_greeting_style(self, traits: Dict[str, float]) -> str:
        """Determine greeting style based on personality traits."""
        formality = traits['formality']
        humor = traits['humor']
        
        if formality > 0.7:
            return "formal"
        elif humor > 0.7:
            return "casual_humorous"
        elif formality < 0.3:
            return "casual"
        else:
            return "neutral"
    
    def _get_response_length(self, traits: Dict[str, float]) -> str:
        """Determine response length based on personality traits."""
        verbosity = traits['verbosity']
        
        if verbosity > 0.8:
            return "verbose"
        elif verbosity > 0.5:
            return "medium"
        elif verbosity > 0.3:
            return "concise"
        else:
            return "minimal"
    
    def _get_technical_level(self, traits: Dict[str, float]) -> str:
        """Determine technical detail level based on personality traits."""
        technical = traits['technical_detail']
        
        if technical > 0.8:
            return "expert"
        elif technical > 0.6:
            return "technical"
        elif technical > 0.4:
            return "balanced"
        elif technical > 0.2:
            return "simplified"
        else:
            return "basic"
    
    def _get_humor_level(self, traits: Dict[str, float]) -> str:
        """Determine humor level based on personality traits."""
        humor = traits['humor']
        
        if humor > 0.8:
            return "high"
        elif humor > 0.5:
            return "medium"
        elif humor > 0.2:
            return "low"
        else:
            return "none"
    
    def _get_formality_level(self, traits: Dict[str, float]) -> str:
        """Determine formality level based on personality traits."""
        formality = traits['formality']
        
        if formality > 0.8:
            return "very_formal"
        elif formality > 0.6:
            return "formal"
        elif formality > 0.4:
            return "neutral"
        elif formality > 0.2:
            return "casual"
        else:
            return "very_casual"
    
    def _get_proactivity_level(self, traits: Dict[str, float]) -> str:
        """Determine proactivity level based on personality traits."""
        proactivity = traits['proactivity']
        
        if proactivity > 0.8:
            return "high"
        elif proactivity > 0.5:
            return "medium"
        elif proactivity > 0.2:
            return "low"
        else:
            return "reactive"
