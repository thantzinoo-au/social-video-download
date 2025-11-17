import os
import re
import unicodedata
from typing import Tuple, Optional


MAX_FILE_SIZE = 300 * 1024 * 1024
MAX_FILENAME_LENGTH = 100


def sanitize_user_id(user_id: str) -> str:
    return "".join(c if c.isalnum() or c in "._-" else "_" for c in str(user_id))


def remove_accents(text: str) -> str:
    nfkd_form = unicodedata.normalize("NFKD", text)

    only_ascii = nfkd_form.encode("ASCII", "ignore").decode("ASCII")

    only_ascii = re.sub(r"[^\w\s.-]", "_", only_ascii)

    only_ascii = re.sub(r"\s+", "_", only_ascii)

    return only_ascii


def create_safe_filename(title: str, video_id: str, max_length: int = MAX_FILENAME_LENGTH) -> str:
    safe_title = remove_accents(title)

    if len(safe_title) > max_length:
        safe_title = safe_title[:max_length]

    return f"{safe_title}_{video_id}"


def validate_file_size(file_size: Optional[int]) -> Tuple[bool, Optional[str]]:
    if file_size is None:
        return True, None

    if file_size > MAX_FILE_SIZE:
        size_mb = file_size / 1024 / 1024
        return False, f"File size {size_mb:.2f}MB exceeds {MAX_FILE_SIZE // 1024 // 1024}MB limit"

    return True, None


def ensure_directory_exists(directory: str) -> None:
    os.makedirs(directory, exist_ok=True)


def get_file_stats(file_path: str) -> dict:
    if not os.path.exists(file_path):
        return {}

    stats = os.stat(file_path)
    return {
        "size": stats.st_size,
        "modified": stats.st_mtime,
        "created": stats.st_ctime,
    }


def validate_url(url: str) -> Tuple[bool, Optional[str]]:
    if not url:
        return False, "URL is required"

    if not url.startswith(("http://", "https://")):
        return False, "URL must start with http:// or https://"

    if len(url) > 2048:
        return False, "URL too long"

    return True, None
