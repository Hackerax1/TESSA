#!/usr/bin/env python3
"""
Knowledge System for TESSA
Tracks user knowledge and provides personalized learning paths
"""

import logging
import json
import os
import time
from typing import Dict, List, Optional, Any, Set

logger = logging.getLogger(__name__)

class KnowledgeSystem:
    """
    A system for tracking user knowledge, providing personalized learning paths,
    and adapting the UI based on user expertise.
    """
    
    def __init__(self, data_dir: str = None):
        """
        Initialize the knowledge system
        
        Args:
            data_dir: Directory to store knowledge data
        """
        self.data_dir = data_dir or os.path.join(os.path.expanduser("~"), ".tessa", "knowledge")
        self.knowledge_areas = self._load_knowledge_areas()
        self.user_knowledge = {}
        self.learning_paths = {}
        
        # Create data directory if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)
        
    def _load_knowledge_areas(self) -> Dict:
        """
        Load knowledge areas from the built-in definitions
        
        Returns:
            Dictionary of knowledge areas
        """
        # Define the knowledge taxonomy
        return {
            "virtualization": {
                "name": "Virtualization",
                "description": "Understanding of virtual machines, containers, and hypervisors",
                "levels": [
                    {"level": 1, "name": "Beginner", "description": "Basic understanding of what VMs are"},
                    {"level": 2, "name": "Intermediate", "description": "Can create and manage VMs"},
                    {"level": 3, "name": "Advanced", "description": "Understands resource allocation and optimization"},
                    {"level": 4, "name": "Expert", "description": "Can troubleshoot complex VM issues and optimize performance"}
                ],
                "related_areas": ["containers", "networking", "storage"],
                "prerequisites": []
            },
            "containers": {
                "name": "Containers",
                "description": "Understanding of container technologies like Docker and LXC",
                "levels": [
                    {"level": 1, "name": "Beginner", "description": "Basic understanding of what containers are"},
                    {"level": 2, "name": "Intermediate", "description": "Can create and run containers"},
                    {"level": 3, "name": "Advanced", "description": "Understands container networking and volumes"},
                    {"level": 4, "name": "Expert", "description": "Can orchestrate containers and optimize performance"}
                ],
                "related_areas": ["virtualization", "networking", "storage"],
                "prerequisites": []
            },
            "networking": {
                "name": "Networking",
                "description": "Understanding of network concepts and configurations",
                "levels": [
                    {"level": 1, "name": "Beginner", "description": "Basic understanding of IP addresses and ports"},
                    {"level": 2, "name": "Intermediate", "description": "Can configure basic network settings"},
                    {"level": 3, "name": "Advanced", "description": "Understands VLANs, routing, and firewalls"},
                    {"level": 4, "name": "Expert", "description": "Can design and troubleshoot complex network setups"}
                ],
                "related_areas": ["virtualization", "containers", "security"],
                "prerequisites": []
            },
            "storage": {
                "name": "Storage",
                "description": "Understanding of storage concepts and technologies",
                "levels": [
                    {"level": 1, "name": "Beginner", "description": "Basic understanding of storage types"},
                    {"level": 2, "name": "Intermediate", "description": "Can configure basic storage options"},
                    {"level": 3, "name": "Advanced", "description": "Understands RAID, LVM, and ZFS"},
                    {"level": 4, "name": "Expert", "description": "Can design and optimize storage solutions"}
                ],
                "related_areas": ["virtualization", "containers", "backup"],
                "prerequisites": []
            },
            "security": {
                "name": "Security",
                "description": "Understanding of security concepts and practices",
                "levels": [
                    {"level": 1, "name": "Beginner", "description": "Basic understanding of authentication and permissions"},
                    {"level": 2, "name": "Intermediate", "description": "Can configure basic security settings"},
                    {"level": 3, "name": "Advanced", "description": "Understands encryption, firewalls, and security best practices"},
                    {"level": 4, "name": "Expert", "description": "Can implement comprehensive security solutions"}
                ],
                "related_areas": ["networking", "backup", "user_management"],
                "prerequisites": ["networking"]
            },
            "backup": {
                "name": "Backup and Recovery",
                "description": "Understanding of backup and recovery concepts and practices",
                "levels": [
                    {"level": 1, "name": "Beginner", "description": "Basic understanding of backups"},
                    {"level": 2, "name": "Intermediate", "description": "Can configure scheduled backups"},
                    {"level": 3, "name": "Advanced", "description": "Understands backup strategies and retention policies"},
                    {"level": 4, "name": "Expert", "description": "Can design and implement comprehensive backup solutions"}
                ],
                "related_areas": ["storage", "security", "virtualization"],
                "prerequisites": ["storage"]
            },
            "user_management": {
                "name": "User Management",
                "description": "Understanding of user management concepts and practices",
                "levels": [
                    {"level": 1, "name": "Beginner", "description": "Basic understanding of users and groups"},
                    {"level": 2, "name": "Intermediate", "description": "Can create and manage users and permissions"},
                    {"level": 3, "name": "Advanced", "description": "Understands role-based access control"},
                    {"level": 4, "name": "Expert", "description": "Can implement complex permission structures"}
                ],
                "related_areas": ["security"],
                "prerequisites": []
            },
            "self_hosting": {
                "name": "Self-Hosting",
                "description": "Understanding of self-hosting concepts and practices",
                "levels": [
                    {"level": 1, "name": "Beginner", "description": "Basic understanding of self-hosting"},
                    {"level": 2, "name": "Intermediate", "description": "Can deploy basic self-hosted services"},
                    {"level": 3, "name": "Advanced", "description": "Understands service dependencies and integration"},
                    {"level": 4, "name": "Expert", "description": "Can design and maintain complex self-hosted environments"}
                ],
                "related_areas": ["virtualization", "containers", "networking", "storage", "security"],
                "prerequisites": ["virtualization", "networking"]
            }
        }
        
    def load_user_knowledge(self, user_id: str) -> Dict:
        """
        Load user knowledge from storage
        
        Args:
            user_id: User ID to load knowledge for
            
        Returns:
            User knowledge dictionary
        """
        knowledge_file = os.path.join(self.data_dir, f"{user_id}_knowledge.json")
        
        if os.path.exists(knowledge_file):
            try:
                with open(knowledge_file, 'r') as f:
                    self.user_knowledge[user_id] = json.load(f)
            except Exception as e:
                logger.error(f"Error loading user knowledge: {e}")
                self.user_knowledge[user_id] = self._create_default_knowledge()
        else:
            self.user_knowledge[user_id] = self._create_default_knowledge()
            
        return self.user_knowledge[user_id]
        
    def save_user_knowledge(self, user_id: str) -> bool:
        """
        Save user knowledge to storage
        
        Args:
            user_id: User ID to save knowledge for
            
        Returns:
            True if successful, False otherwise
        """
        if user_id not in self.user_knowledge:
            return False
            
        knowledge_file = os.path.join(self.data_dir, f"{user_id}_knowledge.json")
        
        try:
            with open(knowledge_file, 'w') as f:
                json.dump(self.user_knowledge[user_id], f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving user knowledge: {e}")
            return False
            
    def _create_default_knowledge(self) -> Dict:
        """
        Create default knowledge structure for a new user
        
        Returns:
            Default knowledge dictionary
        """
        knowledge = {
            "areas": {},
            "expertise_level": "beginner",
            "learning_history": [],
            "completed_tutorials": [],
            "quiz_results": [],
            "last_updated": int(time.time())
        }
        
        # Initialize all knowledge areas at level 1 (beginner)
        for area_id, area in self.knowledge_areas.items():
            knowledge["areas"][area_id] = {
                "level": 1,
                "confidence": 0.5,  # Medium confidence
                "last_assessed": int(time.time()),
                "completed_lessons": []
            }
            
        return knowledge
        
    def get_user_expertise_level(self, user_id: str) -> str:
        """
        Get the overall expertise level of a user
        
        Args:
            user_id: User ID to get expertise level for
            
        Returns:
            Expertise level (beginner, intermediate, advanced, expert)
        """
        if user_id not in self.user_knowledge:
            self.load_user_knowledge(user_id)
            
        return self.user_knowledge[user_id].get("expertise_level", "beginner")
        
    def set_user_expertise_level(self, user_id: str, level: str) -> bool:
        """
        Set the overall expertise level of a user
        
        Args:
            user_id: User ID to set expertise level for
            level: Expertise level (beginner, intermediate, advanced, expert)
            
        Returns:
            True if successful, False otherwise
        """
        if user_id not in self.user_knowledge:
            self.load_user_knowledge(user_id)
            
        if level not in ["beginner", "intermediate", "advanced", "expert"]:
            return False
            
        self.user_knowledge[user_id]["expertise_level"] = level
        self.user_knowledge[user_id]["last_updated"] = int(time.time())
        
        return self.save_user_knowledge(user_id)
        
    def update_knowledge_area(self, user_id: str, area_id: str, level: int, confidence: float = None) -> bool:
        """
        Update a user's knowledge level in a specific area
        
        Args:
            user_id: User ID to update knowledge for
            area_id: Knowledge area ID
            level: Knowledge level (1-4)
            confidence: Confidence in the assessment (0-1)
            
        Returns:
            True if successful, False otherwise
        """
        if user_id not in self.user_knowledge:
            self.load_user_knowledge(user_id)
            
        if area_id not in self.knowledge_areas:
            return False
            
        if level < 1 or level > 4:
            return False
            
        if area_id not in self.user_knowledge[user_id]["areas"]:
            self.user_knowledge[user_id]["areas"][area_id] = {
                "level": 1,
                "confidence": 0.5,
                "last_assessed": int(time.time()),
                "completed_lessons": []
            }
            
        self.user_knowledge[user_id]["areas"][area_id]["level"] = level
        
        if confidence is not None:
            self.user_knowledge[user_id]["areas"][area_id]["confidence"] = max(0, min(1, confidence))
            
        self.user_knowledge[user_id]["areas"][area_id]["last_assessed"] = int(time.time())
        
        # Update overall expertise level based on knowledge areas
        self._update_overall_expertise(user_id)
        
        return self.save_user_knowledge(user_id)
        
    def _update_overall_expertise(self, user_id: str) -> None:
        """
        Update the overall expertise level based on knowledge areas
        
        Args:
            user_id: User ID to update expertise for
        """
        if user_id not in self.user_knowledge:
            return
            
        # Calculate average level across all areas
        areas = self.user_knowledge[user_id]["areas"]
        if not areas:
            return
            
        total_level = sum(area["level"] for area in areas.values())
        avg_level = total_level / len(areas)
        
        # Map average level to expertise level
        if avg_level < 1.5:
            expertise = "beginner"
        elif avg_level < 2.5:
            expertise = "intermediate"
        elif avg_level < 3.5:
            expertise = "advanced"
        else:
            expertise = "expert"
            
        self.user_knowledge[user_id]["expertise_level"] = expertise
        
    def get_knowledge_area_level(self, user_id: str, area_id: str) -> int:
        """
        Get a user's knowledge level in a specific area
        
        Args:
            user_id: User ID to get knowledge for
            area_id: Knowledge area ID
            
        Returns:
            Knowledge level (1-4)
        """
        if user_id not in self.user_knowledge:
            self.load_user_knowledge(user_id)
            
        if area_id not in self.knowledge_areas:
            return 0
            
        if area_id not in self.user_knowledge[user_id]["areas"]:
            return 1
            
        return self.user_knowledge[user_id]["areas"][area_id]["level"]
        
    def record_completed_lesson(self, user_id: str, area_id: str, lesson_id: str) -> bool:
        """
        Record a completed lesson for a user
        
        Args:
            user_id: User ID to record lesson for
            area_id: Knowledge area ID
            lesson_id: Lesson ID
            
        Returns:
            True if successful, False otherwise
        """
        if user_id not in self.user_knowledge:
            self.load_user_knowledge(user_id)
            
        if area_id not in self.knowledge_areas:
            return False
            
        if area_id not in self.user_knowledge[user_id]["areas"]:
            self.user_knowledge[user_id]["areas"][area_id] = {
                "level": 1,
                "confidence": 0.5,
                "last_assessed": int(time.time()),
                "completed_lessons": []
            }
            
        # Add lesson to completed lessons if not already there
        if lesson_id not in self.user_knowledge[user_id]["areas"][area_id]["completed_lessons"]:
            self.user_knowledge[user_id]["areas"][area_id]["completed_lessons"].append(lesson_id)
            
        # Add to learning history
        self.user_knowledge[user_id]["learning_history"].append({
            "type": "lesson",
            "area_id": area_id,
            "lesson_id": lesson_id,
            "timestamp": int(time.time())
        })
        
        return self.save_user_knowledge(user_id)
        
    def record_quiz_result(self, user_id: str, area_id: str, quiz_id: str, score: float) -> bool:
        """
        Record a quiz result for a user
        
        Args:
            user_id: User ID to record quiz for
            area_id: Knowledge area ID
            quiz_id: Quiz ID
            score: Quiz score (0-1)
            
        Returns:
            True if successful, False otherwise
        """
        if user_id not in self.user_knowledge:
            self.load_user_knowledge(user_id)
            
        if area_id not in self.knowledge_areas:
            return False
            
        # Add quiz result
        self.user_knowledge[user_id]["quiz_results"].append({
            "area_id": area_id,
            "quiz_id": quiz_id,
            "score": score,
            "timestamp": int(time.time())
        })
        
        # Update knowledge level based on quiz score
        current_level = self.get_knowledge_area_level(user_id, area_id)
        
        # Adjust level based on score
        if score > 0.8 and current_level < 4:
            # High score, increase level
            self.update_knowledge_area(user_id, area_id, current_level + 1, score)
        elif score < 0.4 and current_level > 1:
            # Low score, decrease level
            self.update_knowledge_area(user_id, area_id, current_level - 1, score)
        else:
            # Update confidence only
            self.update_knowledge_area(user_id, area_id, current_level, score)
            
        return self.save_user_knowledge(user_id)
        
    def get_recommended_learning_path(self, user_id: str) -> Dict:
        """
        Get a personalized learning path for a user
        
        Args:
            user_id: User ID to get learning path for
            
        Returns:
            Learning path dictionary
        """
        if user_id not in self.user_knowledge:
            self.load_user_knowledge(user_id)
            
        # Create a new learning path
        learning_path = {
            "user_id": user_id,
            "created_at": int(time.time()),
            "expertise_level": self.get_user_expertise_level(user_id),
            "recommended_areas": [],
            "next_steps": []
        }
        
        # Find knowledge areas to improve
        for area_id, area in self.knowledge_areas.items():
            user_level = self.get_knowledge_area_level(user_id, area_id)
            
            # Check if prerequisites are met
            prerequisites_met = True
            for prereq_id in area["prerequisites"]:
                prereq_level = self.get_knowledge_area_level(user_id, prereq_id)
                if prereq_level < 2:  # Need at least intermediate level in prerequisites
                    prerequisites_met = False
                    break
                    
            # Add area to recommended areas if prerequisites are met and level is not max
            if prerequisites_met and user_level < 4:
                learning_path["recommended_areas"].append({
                    "area_id": area_id,
                    "name": area["name"],
                    "current_level": user_level,
                    "target_level": min(4, user_level + 1),
                    "priority": 4 - user_level  # Higher priority for lower levels
                })
                
        # Sort recommended areas by priority
        learning_path["recommended_areas"].sort(key=lambda x: x["priority"], reverse=True)
        
        # Generate next steps based on top recommended areas
        for area in learning_path["recommended_areas"][:3]:  # Top 3 areas
            area_id = area["area_id"]
            current_level = area["current_level"]
            target_level = area["target_level"]
            
            # Add next steps based on current and target level
            learning_path["next_steps"].append({
                "area_id": area_id,
                "name": self.knowledge_areas[area_id]["name"],
                "type": "tutorial",
                "level": target_level,
                "description": f"Complete the {self.knowledge_areas[area_id]['levels'][target_level-1]['name']} tutorial for {self.knowledge_areas[area_id]['name']}"
            })
            
            learning_path["next_steps"].append({
                "area_id": area_id,
                "name": self.knowledge_areas[area_id]["name"],
                "type": "quiz",
                "level": target_level,
                "description": f"Take the {self.knowledge_areas[area_id]['levels'][target_level-1]['name']} quiz for {self.knowledge_areas[area_id]['name']}"
            })
            
        # Store the learning path
        self.learning_paths[user_id] = learning_path
        
        return learning_path
        
    def get_ui_complexity_level(self, user_id: str) -> str:
        """
        Get the recommended UI complexity level based on user expertise
        
        Args:
            user_id: User ID to get UI complexity for
            
        Returns:
            UI complexity level (simple, standard, advanced, expert)
        """
        expertise = self.get_user_expertise_level(user_id)
        
        # Map expertise to UI complexity
        if expertise == "beginner":
            return "simple"
        elif expertise == "intermediate":
            return "standard"
        elif expertise == "advanced":
            return "advanced"
        else:  # expert
            return "expert"
            
    def should_show_advanced_features(self, user_id: str, feature_area: str = None) -> bool:
        """
        Determine if advanced features should be shown to the user
        
        Args:
            user_id: User ID to check
            feature_area: Optional specific knowledge area to check
            
        Returns:
            True if advanced features should be shown, False otherwise
        """
        if feature_area:
            # Check specific area
            level = self.get_knowledge_area_level(user_id, feature_area)
            return level >= 3  # Advanced or Expert
        else:
            # Check overall expertise
            expertise = self.get_user_expertise_level(user_id)
            return expertise in ["advanced", "expert"]
            
    def get_explanation_detail_level(self, user_id: str, area_id: str = None) -> str:
        """
        Get the recommended explanation detail level for a user
        
        Args:
            user_id: User ID to get explanation level for
            area_id: Optional specific knowledge area
            
        Returns:
            Explanation detail level (basic, detailed, technical, comprehensive)
        """
        if area_id:
            # Check specific area
            level = self.get_knowledge_area_level(user_id, area_id)
        else:
            # Use overall expertise
            expertise = self.get_user_expertise_level(user_id)
            if expertise == "beginner":
                level = 1
            elif expertise == "intermediate":
                level = 2
            elif expertise == "advanced":
                level = 3
            else:  # expert
                level = 4
                
        # Map level to explanation detail
        if level == 1:
            return "basic"
        elif level == 2:
            return "detailed"
        elif level == 3:
            return "technical"
        else:  # level 4
            return "comprehensive"
            
    def get_knowledge_summary(self, user_id: str) -> Dict:
        """
        Get a summary of the user's knowledge
        
        Args:
            user_id: User ID to get summary for
            
        Returns:
            Knowledge summary dictionary
        """
        if user_id not in self.user_knowledge:
            self.load_user_knowledge(user_id)
            
        summary = {
            "user_id": user_id,
            "expertise_level": self.get_user_expertise_level(user_id),
            "ui_complexity": self.get_ui_complexity_level(user_id),
            "areas": [],
            "strengths": [],
            "areas_for_improvement": [],
            "learning_stats": {
                "completed_lessons": 0,
                "completed_quizzes": 0,
                "average_quiz_score": 0
            }
        }
        
        # Compile area information
        for area_id, area in self.knowledge_areas.items():
            if area_id in self.user_knowledge[user_id]["areas"]:
                user_area = self.user_knowledge[user_id]["areas"][area_id]
                level = user_area["level"]
                confidence = user_area.get("confidence", 0.5)
                
                summary["areas"].append({
                    "area_id": area_id,
                    "name": area["name"],
                    "level": level,
                    "level_name": area["levels"][level-1]["name"],
                    "confidence": confidence,
                    "completed_lessons": len(user_area.get("completed_lessons", []))
                })
                
                # Add to strengths or areas for improvement
                if level >= 3 and confidence >= 0.7:
                    summary["strengths"].append({
                        "area_id": area_id,
                        "name": area["name"],
                        "level": level,
                        "level_name": area["levels"][level-1]["name"]
                    })
                elif level <= 2:
                    summary["areas_for_improvement"].append({
                        "area_id": area_id,
                        "name": area["name"],
                        "level": level,
                        "level_name": area["levels"][level-1]["name"],
                        "target_level": min(4, level + 1),
                        "target_level_name": area["levels"][min(3, level)]["name"]
                    })
        
        # Calculate learning stats
        completed_lessons = sum(len(area.get("completed_lessons", [])) for area in self.user_knowledge[user_id]["areas"].values())
        completed_quizzes = len(self.user_knowledge[user_id].get("quiz_results", []))
        
        summary["learning_stats"]["completed_lessons"] = completed_lessons
        summary["learning_stats"]["completed_quizzes"] = completed_quizzes
        
        if completed_quizzes > 0:
            avg_score = sum(quiz["score"] for quiz in self.user_knowledge[user_id].get("quiz_results", [])) / completed_quizzes
            summary["learning_stats"]["average_quiz_score"] = avg_score
            
        return summary
