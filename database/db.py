
import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple

class DatabaseManager:
    """Manages all database operations"""
    
    def __init__(self, db_path: str = "data/interviews.db"):
        """Initialize database connection"""
        self.db_path = db_path
        self._ensure_data_directory()
        self._initialize_database()
    
    def _ensure_data_directory(self):
        """Create data directory if it doesn't exist"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    def _initialize_database(self):
        """Create tables if they don't exist"""
        schema_path = "database/schema.sql"
        
        if os.path.exists(schema_path):
            with open(schema_path, 'r') as f:
                schema = f.read()
            
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.executescript(schema)
            conn.commit()
            conn.close()
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    # ==================== USER OPERATIONS ====================
    
    def create_user(self, username: str, email: str, password_hash: str) -> bool:
        """Create a new user"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                (username, email, password_hash)
            )
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user by username"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def update_last_login(self, user_id: int):
        """Update user's last login timestamp"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET last_login = ? WHERE user_id = ?",
            (datetime.now(), user_id)
        )
        conn.commit()
        conn.close()
    
    # ==================== INTERVIEW OPERATIONS ====================
    
    def add_interview(self, user_id: int, company_name: str, role: str, 
                     interview_date: str, status: str, preparation_level: int, 
                     notes: str = "", technical_topics: str = "") -> int:
        """Add a new interview record"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO interviews 
               (user_id, company_name, role, interview_date, status, 
                preparation_level, notes, technical_topics)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, company_name, role, interview_date, status, 
             preparation_level, notes, technical_topics)
        )
        interview_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return interview_id
    
    def get_user_interviews(self, user_id: int) -> List[Dict]:
        """Get all interviews for a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT * FROM interviews 
               WHERE user_id = ? 
               ORDER BY interview_date DESC""",
            (user_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def get_interview_by_id(self, interview_id: int) -> Optional[Dict]:
        """Get a specific interview by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM interviews WHERE interview_id = ?", (interview_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def update_interview(self, interview_id: int, company_name: str, role: str,
                        interview_date: str, status: str, preparation_level: int,
                        notes: str, technical_topics: str) -> bool:
        """Update an existing interview"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """UPDATE interviews 
                   SET company_name = ?, role = ?, interview_date = ?, 
                       status = ?, preparation_level = ?, notes = ?, 
                       technical_topics = ?, updated_at = ?
                   WHERE interview_id = ?""",
                (company_name, role, interview_date, status, preparation_level,
                 notes, technical_topics, datetime.now(), interview_id)
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error updating interview: {e}")
            return False
    
    def delete_interview(self, interview_id: int) -> bool:
        """Delete an interview"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM interviews WHERE interview_id = ?", (interview_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error deleting interview: {e}")
            return False
    
    # ==================== ANALYTICS OPERATIONS ====================
    
    def get_status_counts(self, user_id: int) -> Dict[str, int]:
        """Get count of interviews by status"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT status, COUNT(*) as count 
               FROM interviews 
               WHERE user_id = ? 
               GROUP BY status""",
            (user_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        
        result = {status: 0 for status in ['Applied', 'Interviewed', 'Selected', 'Rejected']}
        for row in rows:
            result[row['status']] = row['count']
        return result
    
    def get_weekly_activity(self, user_id: int) -> List[Dict]:
        """Get interview activity for the last 7 days"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT DATE(interview_date) as date, COUNT(*) as count
               FROM interviews
               WHERE user_id = ? 
                 AND interview_date >= date('now', '-7 days')
               GROUP BY DATE(interview_date)
               ORDER BY date""",
            (user_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def get_preparation_stats(self, user_id: int) -> Dict:
        """Get preparation level statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT 
                AVG(preparation_level) as avg_prep,
                MIN(preparation_level) as min_prep,
                MAX(preparation_level) as max_prep,
                COUNT(*) as total_interviews
               FROM interviews
               WHERE user_id = ?""",
            (user_id,)
        )
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else {}
    
    # ==================== SKILL OPERATIONS ====================
    
    def add_interview_skill(self, interview_id: int, skill_name: str, skill_score: int):
        """Add a skill assessment for an interview"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO interview_skills (interview_id, skill_name, skill_score) VALUES (?, ?, ?)",
            (interview_id, skill_name, skill_score)
        )
        conn.commit()
        conn.close()
    
    def get_skill_analysis(self, user_id: int) -> List[Dict]:
        """Get skill performance analysis"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT s.skill_name, AVG(s.skill_score) as avg_score, COUNT(*) as count
               FROM interview_skills s
               JOIN interviews i ON s.interview_id = i.interview_id
               WHERE i.user_id = ?
               GROUP BY s.skill_name
               ORDER BY avg_score ASC""",
            (user_id,)
        )
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]
