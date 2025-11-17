from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import subprocess
import os
import uuid
import json
import time
import logging
import shutil
from functools import wraps
from typing import Tuple, Optional

from config import API_SECRET_KEY, DOWNLOAD_DIR, SECRET_HEADER_NAME, HOST, PORT, DEBUG
from utils import (
    sanitize_user_id,
    create_safe_filename,
    validate_file_size,
    ensure_directory_exists,
    get_file_stats,
    validate_url,
    MAX_FILE_SIZE,
)
from auth import AuthManager

logging.basicConfig(
    level=logging.INFO if not DEBUG else logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("yt-dlp-api")

app = Flask(__name__)
CORS(app)

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["30 per minute"],
    storage_uri="memory://",
    strategy="fixed-window",
)

DEFAULT_FORMAT = "bestvideo+bestaudio/best"
FFMPEG_ARGS = (
    "ffmpeg:-c:v libx264 -profile:v baseline -level 3.0 -preset ultrafast "
    "-crf 23 -c:a aac -b:a 128k -movflags +faststart -threads 6"
)

ensure_directory_exists(DOWNLOAD_DIR)

auth_manager = AuthManager()


def ensure_default_admin():
    admin_username = os.environ.get("ADMIN_USERNAME", "").strip()
    admin_password = os.environ.get("ADMIN_PASSWORD", "").strip()

    if not admin_username or not admin_password:
        logger.info("ADMIN_USERNAME or ADMIN_PASSWORD not set - skipping auto-admin creation")
        return

    if len(admin_password) < 8:
        logger.error("ADMIN_PASSWORD must be at least 8 characters long!")
        return

    conn = None
    try:
        conn = auth_manager._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
        admin_count = cursor.fetchone()[0]

        if admin_count == 0:
            logger.info("No admin user found. Creating default admin from environment variables...")
            success, message = auth_manager.create_user(admin_username, admin_password, "admin")
            if success:
                logger.info(f"✓ Default admin user created: {admin_username}")
                logger.info("You can now login via the web interface or API")
            else:
                logger.error(f"✗ Failed to create default admin: {message}")
        else:
            logger.info(f"Admin user(s) already exist (count: {admin_count})")
    except Exception as e:
        logger.error(f"Error checking/creating admin user: {e}")
    finally:
        if conn:
            auth_manager._put_connection(conn)


ensure_default_admin()


def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get(SECRET_HEADER_NAME)

        if api_key == API_SECRET_KEY:
            request.user = {"id": 0, "username": "legacy", "role": "admin"}
            return f(*args, **kwargs)

        user = auth_manager.validate_api_key(api_key) if api_key else None
        if not user:
            logger.warning(f"Unauthorized access attempt from {request.remote_addr} " f"to {request.endpoint}")
            return jsonify({"error": "Unauthorized access"}), 401

        request.user = user
        return f(*args, **kwargs)

    return decorated_function


def require_session(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        session_token = request.headers.get("X-Session-Token")

        if not session_token:
            return jsonify({"error": "Session token required"}), 401

        user = auth_manager.validate_session(session_token)
        if not user:
            return jsonify({"error": "Invalid or expired session"}), 401

        request.user = user
        return f(*args, **kwargs)

    return decorated_function


def require_auth(f):
    """Decorator that accepts both session tokens and API keys"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Try session token first
        session_token = request.headers.get("X-Session-Token")
        if session_token:
            user = auth_manager.validate_session(session_token)
            if user:
                request.user = user
                return f(*args, **kwargs)

        # Try API key
        api_key = request.headers.get(SECRET_HEADER_NAME)

        if api_key == API_SECRET_KEY:
            request.user = {"id": 0, "username": "legacy", "role": "admin"}
            return f(*args, **kwargs)

        if api_key:
            user = auth_manager.validate_api_key(api_key)
            if user:
                request.user = user
                return f(*args, **kwargs)

        logger.warning(f"Unauthorized access attempt from {request.remote_addr} to {request.endpoint}")
        return jsonify({"error": "Unauthorized access"}), 401

    return decorated_function


def require_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(request, "user") or request.user.get("role") != "admin":
            logger.warning(f"Admin access denied for user: {request.user.get('username', 'unknown')}")
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)

    return decorated_function


def get_user_directory(user_id: str) -> str:
    """Get the general download directory (no longer user-specific)."""
    # All files now go to a single downloads directory
    return DOWNLOAD_DIR


def execute_ytdlp_command(cmd: list) -> Tuple[bool, str, str]:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        success = result.returncode == 0
        return success, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        logger.error(f"Command timed out: {' '.join(cmd)}")
        return False, "", "Command timed out after 5 minutes"
    except Exception as e:
        logger.exception(f"Error executing command: {e}")
        return False, "", str(e)


@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok", "timestamp": time.time(), "download_dir": DOWNLOAD_DIR, "version": "1.0.0"})


@app.route("/auth/login", methods=["POST"])
@limiter.limit("10 per minute")
def login():
    data = request.json
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    user = auth_manager.authenticate_user(username, password)
    if not user:
        logger.warning(f"Failed login attempt for username: {username}")
        return jsonify({"error": "Invalid username or password"}), 401

    session_token = auth_manager.create_session(user["id"])
    if not session_token:
        return jsonify({"error": "Failed to create session"}), 500

    logger.info(f"User logged in: {username}")
    return jsonify(
        {
            "success": True,
            "session_token": session_token,
            "user": {"id": user["id"], "username": user["username"], "role": user["role"]},
        }
    )


@app.route("/auth/logout", methods=["POST"])
@limiter.limit("30 per minute")
@require_session
def logout():
    session_token = request.headers.get("X-Session-Token")

    if auth_manager.invalidate_session(session_token):
        logger.info(f"User logged out: {request.user.get('username')}")
        return jsonify({"success": True, "message": "Logged out successfully"})

    return jsonify({"success": False, "error": "Failed to logout"}), 500


@app.route("/auth/verify", methods=["GET"])
@limiter.limit("60 per minute")
@require_session
def verify_session():
    return jsonify(
        {
            "success": True,
            "user": {"id": request.user["id"], "username": request.user["username"], "role": request.user["role"]},
        }
    )


@app.route("/admin/api-keys", methods=["GET"])
@limiter.limit("30 per minute")
@require_session
@require_admin
def list_all_api_keys():
    keys = auth_manager.list_all_api_keys_admin()
    return jsonify({"success": True, "api_keys": keys, "count": len(keys)})


@app.route("/admin/api-keys/create", methods=["POST"])
@limiter.limit("10 per minute")
@require_session
@require_admin
def create_api_key_admin():
    data = request.json
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    username = data.get("username")
    description = data.get("description", "")
    expires_days = data.get("expires_days")

    if not username:
        return jsonify({"error": "Username is required"}), 400

    conn = None
    try:
        conn = auth_manager._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()

        if not user:
            return jsonify({"error": f"User {username} not found"}), 404

        user_id = user[0]
    finally:
        if conn:
            auth_manager._put_connection(conn)

    success, result = auth_manager.generate_api_key(user_id, description, expires_days)

    if success:
        logger.info(f"Admin {request.user['username']} created API key for user {username}")
        return jsonify({"success": True, "api_key": result, "message": f"API key created for {username}"})

    return jsonify({"success": False, "error": result}), 500


@app.route("/admin/api-keys/<int:key_id>/revoke", methods=["POST"])
@limiter.limit("30 per minute")
@require_session
@require_admin
def revoke_api_key_admin(key_id):
    conn = None
    try:
        conn = auth_manager._get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE api_keys SET is_active = FALSE WHERE id = %s", (key_id,))
        conn.commit()

        if cursor.rowcount > 0:
            logger.info(f"Admin {request.user['username']} revoked API key {key_id}")
            return jsonify({"success": True, "message": "API key revoked successfully"})

        return jsonify({"error": "API key not found"}), 404
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Error revoking API key: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            auth_manager._put_connection(conn)


@app.route("/admin/users", methods=["GET"])
@limiter.limit("30 per minute")
@require_session
@require_admin
def list_users():
    conn = None
    try:
        conn = auth_manager._get_connection()
        from psycopg2.extras import RealDictCursor

        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT id, username, role, created_at, is_active FROM users ORDER BY created_at DESC")
        users = cursor.fetchall()

        users_list = []
        for user in users:
            user_dict = dict(user)
            if user_dict.get("created_at"):
                user_dict["created_at"] = user_dict["created_at"].isoformat()
            users_list.append(user_dict)

        return jsonify({"success": True, "users": users_list, "count": len(users_list)})
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            auth_manager._put_connection(conn)


@app.route("/admin/users/create", methods=["POST"])
@limiter.limit("10 per minute")
@require_session
@require_admin
def create_user_admin():
    data = request.json
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    username = data.get("username")
    password = data.get("password")
    role = data.get("role", "user")

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    success, message = auth_manager.create_user(username, password, role)

    if success:
        logger.info(f"Admin {request.user['username']} created user {username}")
        return jsonify({"success": True, "message": message})

    return jsonify({"success": False, "error": message}), 400


@app.route("/user/api-keys", methods=["GET"])
@limiter.limit("30 per minute")
@require_session
def list_my_api_keys():
    keys = auth_manager.list_api_keys(request.user["id"])
    return jsonify({"success": True, "api_keys": keys, "count": len(keys)})


@app.route("/user/api-keys/create", methods=["POST"])
@limiter.limit("10 per minute")
@require_session
def create_my_api_key():
    data = request.json or {}
    description = data.get("description", "")
    expires_days = data.get("expires_days")

    success, result = auth_manager.generate_api_key(request.user["id"], description, expires_days)

    if success:
        logger.info(f"User {request.user['username']} created API key")
        return jsonify({"success": True, "api_key": result, "message": "API key created successfully"})

    return jsonify({"success": False, "error": result}), 500


@app.route("/user/api-keys/<int:key_id>/revoke", methods=["POST"])
@limiter.limit("30 per minute")
@require_session
def revoke_my_api_key(key_id):
    success, message = auth_manager.revoke_api_key(key_id, request.user["id"])

    if success:
        logger.info(f"User {request.user['username']} revoked API key {key_id}")
        return jsonify({"success": True, "message": message})

    return jsonify({"success": False, "error": message}), 400


@app.route("/user/api-key-status", methods=["GET"])
@limiter.limit("60 per minute")
@require_session
def check_api_key_status():
    """Check if the current user has an active API key."""
    user_id = request.user["id"]

    conn = None
    try:
        conn = auth_manager._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """SELECT COUNT(*) FROM api_keys 
               WHERE user_id = %s AND is_active = TRUE 
               AND (expires_at IS NULL OR expires_at > NOW())""",
            (user_id,),
        )
        active_key_count = cursor.fetchone()[0]

        has_api_key = active_key_count > 0

        return jsonify(
            {
                "success": True,
                "has_api_key": has_api_key,
                "is_active": has_api_key,
            }
        )
    except Exception as e:
        logger.error(f"Error checking API key status: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        if conn:
            auth_manager._put_connection(conn)


@app.route("/download", methods=["POST"])
@limiter.limit("30 per minute")
@require_auth
def download_video():
    data = request.json
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    video_url = data.get("url")
    if not video_url:
        return jsonify({"error": "URL is required"}), 400

    is_valid, error_msg = validate_url(video_url)
    if not is_valid:
        return jsonify({"error": error_msg}), 400

    # Use authenticated user's ID for directory creation
    user_id = request.user["id"]
    user_dir = get_user_directory(user_id)

    output_format = data.get("format", DEFAULT_FORMAT)
    request_id = str(uuid.uuid4())

    logger.info(
        f"Download request - URL: {video_url}, Format: {output_format}, "
        f"User: {request.user['username']} (ID: {user_id}), RequestID: {request_id}"
    )

    try:
        info_cmd = ["yt-dlp", "--dump-json", "--no-playlist", video_url]
        success, stdout, stderr = execute_ytdlp_command(info_cmd)

        if not success:
            logger.error(f"Error getting video info: {stderr}")
            return jsonify({"success": False, "error": f"Failed to get video info: {stderr}"}), 500

        try:
            video_info = json.loads(stdout)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse video info JSON: {e}")
            return jsonify({"success": False, "error": "Invalid video metadata"}), 500

        file_size = video_info.get("filesize") or video_info.get("filesize_approx")
        is_valid, error_msg = validate_file_size(file_size)
        if not is_valid:
            logger.warning(f"File size validation failed: {error_msg}")
            return jsonify({"success": False, "error": error_msg}), 400

        original_title = video_info.get("title", "video")
        video_id = video_info.get("id", "unknown")

        # Generate UUID4 for stored filename
        stored_filename = str(uuid.uuid4())
        filename_template = f"{user_dir}/{stored_filename}.%(ext)s"

        download_cmd = [
            "yt-dlp",
            "-f",
            output_format,
            "-o",
            filename_template,
            "--no-playlist",
            "--merge-output-format",
            "mp4",
            "--postprocessor-args",
            FFMPEG_ARGS,
            video_url,
        ]

        logger.info(f"Executing download: {' '.join(download_cmd)}")
        success, stdout, stderr = execute_ytdlp_command(download_cmd)

        if not success:
            logger.error(f"Download failed: {stderr}")
            return jsonify({"success": False, "error": f"Download failed: {stderr}"}), 500

        # Get actual downloaded file path
        actual_file_path = f"{user_dir}/{stored_filename}.mp4"

        # Get file size
        file_size = 0
        if os.path.exists(actual_file_path):
            file_size = os.path.getsize(actual_file_path)

        # Create original filename from title
        safe_title = create_safe_filename(original_title, video_id)
        original_filename = f"{safe_title}.mp4"

        # Insert into database
        conn = None
        try:
            conn = auth_manager._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO downloaded_files 
                   (user_id, original_filename, stored_filename, file_path, file_size, 
                    mime_type, video_title, video_url)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                   RETURNING id""",
                (
                    user_id,
                    original_filename,
                    f"{stored_filename}.mp4",
                    actual_file_path,
                    file_size,
                    "video/mp4",
                    original_title,
                    video_url,
                ),
            )
            file_record_id = cursor.fetchone()[0]
            conn.commit()
            logger.info(f"Saved file record to database: {file_record_id}")
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Error saving file to database: {e}")
        finally:
            if conn:
                auth_manager._put_connection(conn)

        logger.info(f"Video downloaded successfully: {stored_filename}.mp4")

        return jsonify(
            {
                "success": True,
                "request_id": request_id,
                "user_id": user_id,
                "video_id": video_info.get("id"),
                "title": original_title,
                "file_path": f"{stored_filename}.mp4",
                "duration": video_info.get("duration"),
                "download_path": f"/files/{stored_filename}.mp4",
            }
        )

    except Exception as e:
        logger.exception(f"Exception during download: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/files/<path:file_path>", methods=["GET"])
@limiter.limit("30 per minute")
@require_auth
def get_file(file_path):
    full_path = os.path.join(DOWNLOAD_DIR, file_path)

    real_download_dir = os.path.realpath(DOWNLOAD_DIR)
    real_file_path = os.path.realpath(full_path)

    if not real_file_path.startswith(real_download_dir):
        logger.warning(f"Path traversal attempt: {file_path}")
        return jsonify({"error": "Invalid file path"}), 403

    if not os.path.exists(full_path):
        return jsonify({"error": "File not found"}), 404

    return send_file(full_path, as_attachment=True)


@app.route("/list-files", methods=["GET"])
@limiter.limit("30 per minute")
@require_auth
def list_user_files():
    # Use authenticated user's ID
    user_id = request.user["id"]

    conn = None
    try:
        conn = auth_manager._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT id, original_filename, stored_filename, file_path, file_size, 
                      created_at, video_title, video_url
               FROM downloaded_files 
               WHERE user_id = %s 
               ORDER BY created_at DESC""",
            (user_id,),
        )
        files = cursor.fetchall()

        result = []
        for file in files:
            file_id, original_filename, stored_filename, file_path, file_size, created_at, video_title, video_url = file

            # Convert created_at to timestamp
            modified_timestamp = created_at.timestamp() if created_at else 0

            result.append(
                {
                    "id": str(file_id),
                    "name": original_filename,
                    "path": stored_filename,
                    "size": file_size,
                    "modified": modified_timestamp,
                    "download_path": f"/files/{stored_filename}",
                    "title": video_title,
                }
            )

        return jsonify({"success": True, "user_id": str(user_id), "files": result, "count": len(result)})
    except Exception as e:
        logger.error(f"Error listing files for user {user_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        if conn:
            auth_manager._put_connection(conn)


@app.route("/delete-file", methods=["DELETE"])
@limiter.limit("30 per minute")
@require_auth
def delete_file():
    data = request.json
    if not data or "file_path" not in data:
        return jsonify({"error": "file_path is required"}), 400

    file_path = data["file_path"]
    user_id = request.user["id"]

    conn = None
    try:
        conn = auth_manager._get_connection()
        cursor = conn.cursor()

        # Get file record from database
        cursor.execute(
            """SELECT id, stored_filename, file_path 
               FROM downloaded_files 
               WHERE user_id = %s AND stored_filename = %s""",
            (user_id, file_path),
        )
        file_record = cursor.fetchone()

        if not file_record:
            return jsonify({"error": "File not found or unauthorized"}), 404

        file_id, stored_filename, actual_file_path = file_record

        # Delete from database
        cursor.execute("DELETE FROM downloaded_files WHERE id = %s", (file_id,))
        conn.commit()

        # Delete physical file
        if os.path.exists(actual_file_path):
            try:
                os.remove(actual_file_path)
                logger.info(f"Deleted file: {actual_file_path}")
            except Exception as e:
                logger.warning(f"Failed to delete physical file {actual_file_path}: {e}")

        return jsonify({"success": True, "message": "File deleted successfully"})
    except Exception as e:
        if conn:
            conn.rollback()
        logger.exception(f"Error deleting file: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        if conn:
            auth_manager._put_connection(conn)


@app.route("/formats", methods=["POST"])
@limiter.limit("30 per minute")
@require_auth
def list_formats():
    data = request.json
    if not data or "url" not in data:
        return jsonify({"error": "URL is required"}), 400

    video_url = data["url"]

    is_valid, error_msg = validate_url(video_url)
    if not is_valid:
        return jsonify({"error": error_msg}), 400

    try:
        cmd = ["yt-dlp", "-F", "--no-playlist", video_url]
        success, stdout, stderr = execute_ytdlp_command(cmd)

        if not success:
            logger.error(f"Error fetching formats: {stderr}")
            return jsonify({"success": False, "error": stderr}), 500

        formats = []
        for line in stdout.strip().split("\n"):
            if not line or line.startswith("[") or "ID" in line:
                continue

            parts = line.split(maxsplit=1)
            if len(parts) >= 2 and parts[0].replace("+", "").isdigit():
                formats.append({"format_id": parts[0], "description": parts[1] if len(parts) > 1 else ""})

        return jsonify({"success": True, "formats": formats, "count": len(formats), "raw_output": stdout})

    except Exception as e:
        logger.exception(f"Error in list_formats: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/disk-usage", methods=["GET"])
@limiter.limit("30 per minute")
@require_auth
def get_disk_usage():
    try:
        usage = shutil.disk_usage(DOWNLOAD_DIR)

        dir_size = 0
        try:
            for root, _, files in os.walk(DOWNLOAD_DIR):
                for file in files:
                    file_path = os.path.join(root, file)
                    if os.path.exists(file_path):
                        dir_size += os.path.getsize(file_path)
        except Exception as e:
            logger.warning(f"Error calculating directory size: {e}")

        return jsonify(
            {
                "success": True,
                "total_space": usage.total,
                "used_space": usage.used,
                "free_space": usage.free,
                "usage_percent": round(usage.used / usage.total * 100, 2),
                "download_dir_size": dir_size,
            }
        )
    except Exception as e:
        logger.exception(f"Error getting disk usage: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(429)
def ratelimit_handler(e):
    logger.warning(f"Rate limit exceeded from {request.remote_addr} - {e.description}")
    return (
        jsonify(
            {
                "error": "Rate limit exceeded",
                "message": "Too many requests. Please try again later.",
                "retry_after": e.description,
            }
        ),
        429,
    )


@app.errorhandler(500)
def internal_error(error):
    logger.exception("Internal server error")
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    from config import Config

    Config.log_config()
    logger.info(f"Starting yt-dlp API server on {HOST}:{PORT}")
    logger.info(f"Debug mode: {DEBUG}")

    app.run(host=HOST, port=PORT, debug=DEBUG)
