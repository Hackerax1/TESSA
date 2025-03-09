"""
Audit logging module for Proxmox NLI.
Handles logging of all commands and their results for security and compliance.
"""
import os
import json
from datetime import datetime
from loguru import logger
import sqlite3
from typing import Dict, Any

class AuditLogger:
    def __init__(self, log_dir: str = None):
        """Initialize the audit logger"""
        self.log_dir = log_dir or os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'logs')
        os.makedirs(self.log_dir, exist_ok=True)

        # Configure file logging
        log_file = os.path.join(self.log_dir, 'audit.log')
        logger.add(log_file, 
                  rotation="1 day",
                  retention="90 days",
                  format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")

        # Initialize SQLite database for structured audit logs
        self.db_path = os.path.join(self.log_dir, 'audit.db')
        self._init_db()

    def _init_db(self):
        """Initialize the SQLite database for audit logs"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    user TEXT,
                    query TEXT NOT NULL,
                    intent TEXT NOT NULL,
                    entities TEXT,
                    result TEXT,
                    success INTEGER,
                    source TEXT,
                    ip_address TEXT
                )
            ''')
            conn.commit()

    def log_command(self, 
                    query: str,
                    intent: str,
                    entities: Dict[str, Any],
                    result: Dict[str, Any],
                    user: str = None,
                    source: str = 'cli',
                    ip_address: str = None):
        """
        Log a command execution with all relevant details
        
        Args:
            query: The original natural language query
            intent: The identified intent
            entities: Extracted entities from the query
            result: The result of command execution
            user: The user who executed the command
            source: Source of the command (cli/web)
            ip_address: IP address for web requests
        """
        timestamp = datetime.now().isoformat()
        
        # Log to file
        log_entry = {
            'timestamp': timestamp,
            'user': user,
            'query': query,
            'intent': intent,
            'entities': entities,
            'result': result,
            'source': source,
            'ip_address': ip_address
        }
        
        logger.info("Command execution: {}", json.dumps(log_entry, indent=2))
        
        # Store in database
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO audit_log 
                (timestamp, user, query, intent, entities, result, success, source, ip_address)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                timestamp,
                user,
                query,
                intent,
                json.dumps(entities),
                json.dumps(result),
                1 if result.get('success', False) else 0,
                source,
                ip_address
            ))
            conn.commit()

    def get_recent_logs(self, limit: int = 100) -> list:
        """Get recent audit logs from the database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT timestamp, user, query, intent, entities, result, success, source, ip_address
                FROM audit_log
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
            
            columns = ['timestamp', 'user', 'query', 'intent', 'entities', 'result', 'success', 'source', 'ip_address']
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_user_activity(self, user: str, limit: int = 100) -> list:
        """Get recent activity for a specific user"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT timestamp, query, intent, entities, result, success, source, ip_address
                FROM audit_log
                WHERE user = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (user, limit))
            
            columns = ['timestamp', 'query', 'intent', 'entities', 'result', 'success', 'source', 'ip_address']
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_failed_commands(self, limit: int = 100) -> list:
        """Get recent failed command executions"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT timestamp, user, query, intent, entities, result, source, ip_address
                FROM audit_log
                WHERE success = 0
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
            
            columns = ['timestamp', 'user', 'query', 'intent', 'entities', 'result', 'source', 'ip_address']
            return [dict(zip(columns, row)) for row in cursor.fetchall()]