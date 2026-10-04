import logging
import os

from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)


def remove_stored_files(upload_folder, filename, keep=None):
    """
    Remove saved copies of a document. Files are stored as "<uuid hex>_<filename>".
    """
    safe_name = secure_filename(filename)

    if not safe_name or not os.path.isdir(upload_folder):
        return

    for stored_name in os.listdir(upload_folder):
        prefix, _, original_name = stored_name.partition("_")

        if stored_name == keep:
            continue

        if original_name == safe_name and len(prefix) == 32:
            try:
                os.remove(os.path.join(upload_folder, stored_name))
            except OSError:
                logger.warning("Could not remove stored file %s", stored_name)
