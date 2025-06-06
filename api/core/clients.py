# ******************** client configurations ********************#
"""
Global client configurations for external services.
"""

import logging
from pathlib import Path
import sys

# Add project paths to Python path
curr_dir = Path(__file__).parent
lib_path = curr_dir / ".." / ".." / "lib"
data_path = curr_dir / ".." / ".." / "data"
sys.path.insert(0, str(lib_path))
sys.path.insert(0, str(data_path))

from lib.config import get_config, get_openai_client, get_typesense_client

# ******************** configuration and logging ********************#
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ******************** global configuration and clients ********************#
config = get_config()
openai_client = get_openai_client()
typesense_client = get_typesense_client()
