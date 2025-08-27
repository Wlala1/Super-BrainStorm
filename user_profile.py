import psycopg2
from psycopg2.extras import RealDictCursor
import json
import time
from typing import Dict, List, Optional
from config import Config

class UserProfile:
    def __init__(self):
        self.connection = None
        self._connect()
    
    def _connect(self):
        """Establish a database connection."""
        try:
            self.connection = psycopg2.connect(
                host=Config.DB_HOST,
                port=Config.DB_PORT,
                database=Config.DB_NAME,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                cursor_factory=RealDictCursor
            )
            print("Database connection established")
        except Exception as e:
            print(f"Database connection failed: {e}")
            self.connection = None
    
    def get_user_history(self, user_id: str) -> Dict:
        """Query a user's historical behavior and preferences."""
        if not self.connection:
            return self._default_profile()
        
        try:
            with self.connection.cursor() as cur:
                cur.execute("""
                    SELECT interests, recent_topics, preferences, interaction_history
                    FROM user_profiles 
                    WHERE user_id = %s
                """, (user_id,))
                
                result = cur.fetchone()
                if result:
                    return {
                        "interest_keywords": json.loads(result['interests'] or '[]'),
                        "recent_topics": json.loads(result['recent_topics'] or '[]'),
                        "preferences": json.loads(result['preferences'] or '{}'),
                        "interaction_history": json.loads(result['interaction_history'] or '[]')
                    }
        except Exception as e:
            print(f"Failed to fetch user history: {e}")
        
        return self._default_profile()
    
    def update_user_interaction(self, user_id: str, topic: str, selected_ideas: List[str]):
        """Update the user's interaction records."""
        if not self.connection:
            return
        
        try:
            with self.connection.cursor() as cur:
                interaction_record = {
                    "topic": topic,
                    "selected_ideas": selected_ideas,
                    "timestamp": time.time()
                }
                
                # Insert or update the user's record
                cur.execute("""
                    INSERT INTO user_profiles (user_id, recent_topics, interaction_history)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (user_id) 
                    DO UPDATE SET 
                        recent_topics = (
                            COALESCE(user_profiles.recent_topics, '[]'::jsonb) || %s::jsonb
                        )[greatest(0, jsonb_array_length(COALESCE(user_profiles.recent_topics, '[]'::jsonb)) - 9):],
                        interaction_history = (
                            COALESCE(user_profiles.interaction_history, '[]'::jsonb) || %s::jsonb
                        )[greatest(0, jsonb_array_length(COALESCE(user_profiles.interaction_history, '[]'::jsonb)) - 49):],
                        updated_at = NOW()
                """, (
                    user_id,
                    json.dumps([topic]),
                    json.dumps([interaction_record]),
                    json.dumps([topic]),
                    json.dumps([interaction_record])
                ))
                self.connection.commit()
                print(f"Updated interaction history for user {user_id}")
        except Exception as e:
            print(f"Failed to update user interaction history: {e}")
            if self.connection:
                self.connection.rollback()
    
    def _default_profile(self) -> Dict:
        """Return a default user profile."""
        return {
            "interest_keywords": [],
            "recent_topics": [],
            "preferences": {},
            "interaction_history": []
        }