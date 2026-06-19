

from supabase import create_client
import logging
import os
import traceback
from pathlib import Path
from io import BufferedReader, FileIO
from django.db.models.fields.files import FieldFile

logger = logging.getLogger(__name__)

# Read env vars but avoid creating a client at import-time if values are missing/invalid.
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
BUCKET_NAME = os.environ.get('SUPABASE_BUCKET_NAME', 'product-images')

# Build public url only when SUPABASE_URL looks valid
if SUPABASE_URL and SUPABASE_URL.startswith('http'):
    SUPABASE_PUBLIC_URL = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}"
else:
    SUPABASE_PUBLIC_URL = None

# Lazy-safe client creation: protect against invalid URL/keys so imports (e.g. migrations)
# don't fail. If creation fails, `supabase` stays None and upload functions raise clear errors.
supabase = None
if SUPABASE_URL and SUPABASE_KEY and SUPABASE_URL.startswith('http'):
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
        supabase = None


def get_public_url(filepath):
    """Convert any file path to a valid Supabase public URL.

    Returns an empty string when Supabase is not configured.
    """
    if not filepath:
        return ''

    # If Supabase public URL isn't configured, return empty rather than raising
    if not SUPABASE_PUBLIC_URL:
        return ''

    # Normalize path
    filepath = filepath.replace("\\", "/").lstrip("/")

    # If already a full URL, return as-is
    if filepath.startswith("http"):
        return filepath

    return f"{SUPABASE_PUBLIC_URL}/{filepath}"


def _normalize_upload_file(file):
    if isinstance(file, FieldFile):
        if not file.name:
            raise ValueError('Cannot upload empty Django FieldFile')
        if hasattr(file, 'path') and file.path:
            return Path(file.path)
        file = file.file

    if isinstance(file, (BufferedReader, FileIO)):
        return file

    if isinstance(file, bytes):
        return file

    if hasattr(file, 'read'):
        return file

    return Path(file)


def upload_image(file, filename):
    if supabase is None:
        raise RuntimeError('SUPABASE_URL and SUPABASE_KEY must be set to upload images.')

    try:
        filename = filename.replace("\\", "/")
        upload_file = _normalize_upload_file(file)

        if isinstance(upload_file, Path):
            if not upload_file.exists():
                raise FileNotFoundError(f"Upload file not found: {upload_file}")
            upload_file = str(upload_file)

        logger.debug("Uploading file to Supabase: %s (type=%s)", filename, type(upload_file))

        response = supabase.storage.from_(BUCKET_NAME).upload(
            path=filename,
            file=upload_file
        )

        if not response or not getattr(response, "full_path", None):
            raise RuntimeError("Supabase upload failed or returned no path")

        if not supabase.storage.from_(BUCKET_NAME).exists(filename):
            raise RuntimeError(f"Uploaded file not found in bucket: {filename}")

        public_url = supabase.storage.from_(BUCKET_NAME).get_public_url(filename)
        return public_url

    except Exception as e:
        logger.exception("Supabase upload failed for %s", filename)
        return None

        
    
    # except Exception as e:
    #     print("UPLOAD ERROR:", e)
    #     return None