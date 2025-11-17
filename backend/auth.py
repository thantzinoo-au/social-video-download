import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
import secrets
import hashlib
import os
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
import logging

logger = logging.getLogger("yt-dlp-api.auth")

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = int(os.environ.get("DB_PORT", 5432))
DB_NAME = os.environ.get("DB_NAME", "social_video_db")
DB_USER = os.environ.get("DB_USER", "videouser")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "changeme123")


class AuthManager:
    def __init__(self):
        self.db_host = DB_HOST
        self.db_port = DB_PORT
        self.db_name = DB_NAME
        self.db_user = DB_USER
        self.db_password = DB_PASSWORD

        try:
            self.connection_pool = psycopg2.pool.SimpleConnectionPool(
                1,
                20,
                host=self.db_host,
                port=self.db_port,
                database=self.db_name,
                user=self.db_user,
                password=self.db_password,
            )
            logger.info(f"Connected to PostgreSQL database: {self.db_name}")
        except Exception as e:
            logger.error(f"Failed to create connection pool: {e}")
            raise

        self._init_db()

    def _get_connection(self):
        try:
            conn = self.connection_pool.getconn()
            return conn
        except Exception as e:
            logger.error(f"Failed to get connection from pool: {e}")
            raise

    def _put_connection(self, conn):
        if conn:
            self.connection_pool.putconn(conn)

    def _init_db(self):
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Enable uuid extension
            cursor.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    username VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    role VARCHAR(50) NOT NULL DEFAULT 'user',
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE
                )
            """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS api_keys (
                    id SERIAL PRIMARY KEY,
                    user_id UUID NOT NULL,
                    api_key VARCHAR(255) UNIQUE NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id SERIAL PRIMARY KEY,
                    user_id UUID NOT NULL,
                    session_token VARCHAR(255) UNIQUE NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS downloaded_files (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    user_id UUID NOT NULL,
                    original_filename VARCHAR(500) NOT NULL,
                    stored_filename VARCHAR(255) NOT NULL,
                    file_path TEXT NOT NULL,
                    file_size BIGINT NOT NULL DEFAULT 0,
                    mime_type VARCHAR(100),
                    video_title TEXT,
                    video_url TEXT,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            """
            )

            cursor.execute("CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_api_keys_api_key ON api_keys(api_key)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(session_token)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_downloaded_files_user_id ON downloaded_files(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_downloaded_files_created_at ON downloaded_files(created_at)")

            conn.commit()
            logger.info("Database initialized successfully")
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Error initializing database: {e}")
            raise
        finally:
            if conn:
                self._put_connection(conn)

    def _hash_password(self, password: str) -> str:
        salt = secrets.token_hex(16)
        pwd_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}${pwd_hash}"

    def _verify_password(self, password: str, password_hash: str) -> bool:
        try:
            salt, pwd_hash = password_hash.split("$")
            test_hash = hashlib.sha256((password + salt).encode()).hexdigest()
            return test_hash == pwd_hash
        except Exception:
            return False

    def create_user(self, username: str, password: str, role: str = "user") -> Tuple[bool, str]:
        if role not in ["admin", "user"]:
            return False, "Invalid role. Must be 'admin' or 'user'"

        if len(password) < 8:
            return False, "Password must be at least 8 characters long"

        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            password_hash = self._hash_password(password)

            cursor.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
                (username, password_hash, role),
            )
            conn.commit()
            logger.info(f"Created user: {username} with role: {role}")
            return True, f"User {username} created successfully"
        except psycopg2.IntegrityError:
            if conn:
                conn.rollback()
            return False, f"Username {username} already exists"
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Error creating user: {e}")
            return False, str(e)
        finally:
            if conn:
                self._put_connection(conn)

    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT * FROM users WHERE username = %s AND is_active = TRUE", (username,))
            user = cursor.fetchone()

            if user and self._verify_password(password, user["password_hash"]):
                return {
                    "id": user["id"],
                    "username": user["username"],
                    "role": user["role"],
                    "created_at": user["created_at"].isoformat() if user["created_at"] else None,
                }
            return None
        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            return None
        finally:
            if conn:
                self._put_connection(conn)

    def create_session(self, user_id: int, duration_hours: int = 24) -> Optional[str]:
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            session_token = secrets.token_urlsafe(32)
            expires_at = datetime.utcnow() + timedelta(hours=duration_hours)

            cursor.execute(
                """INSERT INTO sessions (user_id, session_token, expires_at)
                   VALUES (%s, %s, %s)""",
                (user_id, session_token, expires_at),
            )
            conn.commit()
            logger.info(f"Created session for user_id: {user_id}")
            return session_token
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Error creating session: {e}")
            return None
        finally:
            if conn:
                self._put_connection(conn)

    def validate_session(self, session_token: str) -> Optional[Dict]:
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(
                """SELECT s.*, u.username, u.role 
                   FROM sessions s 
                   JOIN users u ON s.user_id = u.id
                   WHERE s.session_token = %s AND s.is_active = TRUE""",
                (session_token,),
            )
            session = cursor.fetchone()

            if not session:
                return None

            if datetime.utcnow() > session["expires_at"]:
                cursor.execute("UPDATE sessions SET is_active = FALSE WHERE id = %s", (session["id"],))
                conn.commit()
                return None

            return {"id": session["user_id"], "username": session["username"], "role": session["role"]}
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Error validating session: {e}")
            return None
        finally:
            if conn:
                self._put_connection(conn)

    def invalidate_session(self, session_token: str) -> bool:
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE sessions SET is_active = FALSE WHERE session_token = %s", (session_token,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Error invalidating session: {e}")
            return False
        finally:
            if conn:
                self._put_connection(conn)

    def generate_api_key(
        self, user_id: int, description: str = "", expires_days: Optional[int] = None
    ) -> Tuple[bool, str]:
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            api_key = "sk_" + secrets.token_urlsafe(32)
            expires_at = None

            if expires_days:
                expires_at = datetime.utcnow() + timedelta(days=expires_days)

            cursor.execute(
                """INSERT INTO api_keys (user_id, api_key, description, expires_at)
                   VALUES (%s, %s, %s, %s)""",
                (user_id, api_key, description, expires_at),
            )
            conn.commit()
            logger.info(f"Generated API key for user_id: {user_id}")
            return True, api_key
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Error generating API key: {e}")
            return False, str(e)
        finally:
            if conn:
                self._put_connection(conn)

    def validate_api_key(self, api_key: str) -> Optional[Dict]:
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(
                """SELECT k.*, u.username, u.role 
                   FROM api_keys k 
                   JOIN users u ON k.user_id = u.id
                   WHERE k.api_key = %s AND k.is_active = TRUE AND u.is_active = TRUE""",
                (api_key,),
            )
            key_record = cursor.fetchone()

            if not key_record:
                return None

            if key_record["expires_at"]:
                if datetime.utcnow() > key_record["expires_at"]:
                    return None

            return {"id": key_record["user_id"], "username": key_record["username"], "role": key_record["role"]}
        except Exception as e:
            logger.error(f"Error validating API key: {e}")
            return None
        finally:
            if conn:
                self._put_connection(conn)

    def list_api_keys(self, user_id: int) -> List[Dict]:
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(
                """SELECT id, api_key, description, created_at, expires_at, is_active
                   FROM api_keys WHERE user_id = %s
                   ORDER BY created_at DESC""",
                (user_id,),
            )
            keys = cursor.fetchall()

            result = []
            for key in keys:
                masked_key = key["api_key"][:8] + "..." + key["api_key"][-4:]

                result.append(
                    {
                        "id": key["id"],
                        "api_key": masked_key,
                        "description": key["description"],
                        "created_at": key["created_at"].isoformat() if key["created_at"] else None,
                        "expires_at": key["expires_at"].isoformat() if key["expires_at"] else None,
                        "is_active": key["is_active"],
                        "is_expired": (key["expires_at"] < datetime.utcnow() if key["expires_at"] else False),
                    }
                )

            return result
        except Exception as e:
            logger.error(f"Error listing API keys: {e}")
            return []
        finally:
            if conn:
                self._put_connection(conn)

    def revoke_api_key(self, key_id: int, user_id: int) -> Tuple[bool, str]:
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE api_keys SET is_active = FALSE WHERE id = %s AND user_id = %s", (key_id, user_id))
            conn.commit()

            if cursor.rowcount > 0:
                logger.info(f"Revoked API key {key_id} for user {user_id}")
                return True, "API key revoked successfully"
            return False, "API key not found or unauthorized"
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Error revoking API key: {e}")
            return False, str(e)
        finally:
            if conn:
                self._put_connection(conn)

    def list_all_api_keys_admin(self) -> List[Dict]:
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(
                """SELECT k.*, u.username 
                   FROM api_keys k 
                   JOIN users u ON k.user_id = u.id
                   ORDER BY k.created_at DESC"""
            )
            keys = cursor.fetchall()

            result = []
            for key in keys:
                masked_key = key["api_key"][:8] + "..." + key["api_key"][-4:]

                result.append(
                    {
                        "id": key["id"],
                        "username": key["username"],
                        "api_key": masked_key,
                        "description": key["description"],
                        "created_at": key["created_at"].isoformat() if key["created_at"] else None,
                        "expires_at": key["expires_at"].isoformat() if key["expires_at"] else None,
                        "is_active": key["is_active"],
                        "is_expired": (key["expires_at"] < datetime.utcnow() if key["expires_at"] else False),
                    }
                )

            return result
        except Exception as e:
            logger.error(f"Error listing all API keys: {e}")
            return []
        finally:
            if conn:
                self._put_connection(conn)

    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT id, username, role, created_at FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()

            if user:
                return dict(user)
            return None
        except Exception as e:
            logger.error(f"Error getting user by ID: {e}")
            return None
        finally:
            if conn:
                self._put_connection(conn)
