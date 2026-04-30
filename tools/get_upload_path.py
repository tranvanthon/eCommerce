import os, uuid

# make path
def get_upload_path(instance, filename):
    """
    Generate a unique upload path for media files.
    """
    ext = filename.split('.')[-1]
    unique_filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('uploads', unique_filename)
