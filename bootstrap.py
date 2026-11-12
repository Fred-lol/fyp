from functools import lru_cache
import ipaddress
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from urllib.parse import urlparse

import streamlit as st
from PIL import Image

from database.schema import initialize_schema
from services.box_service import ensure_box_templates


PROJECT_DIR = Path(__file__).resolve().parent
_ORIGINAL_SET_PAGE_CONFIG = st.set_page_config


def _is_local_tracking_host(host: str | None) -> bool:
    """Only launch a service that belongs to this machine/network."""
    if not host or host.lower() in {"localhost", "127.0.0.1", "0.0.0.0", "::1"}:
        return True
    try:
        return ipaddress.ip_address(host).is_private
    except ValueError:
        return False


@lru_cache(maxsize=1)
def ensure_tracking_api() -> bool:
    """Start the local tracking API once when AquaLoad starts.

    The desktop launcher already does this, but this safeguard also covers
    developers starting Streamlit directly. Remote production API URLs are
    deliberately left untouched.
    """
    # A managed host can start the API beside Streamlit with start_web.sh.
    # Do not create a second API process in that environment.
    if os.getenv("AQUALOAD_MANAGED_TRACKING_API") == "1":
        return True

    configured_url = os.getenv("AQUALOAD_TRACKING_API", "http://127.0.0.1:8000")
    parsed = urlparse(configured_url)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or 8000
    if not _is_local_tracking_host(host):
        return False
    try:
        with socket.create_connection((host, port), timeout=0.2):
            return True
    except OSError:
        pass

    creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "tracking_api:app", "--host", "0.0.0.0", "--port", str(port)],
            cwd=PROJECT_DIR,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creation_flags,
        )
    except OSError:
        return False

    for _ in range(15):
        time.sleep(0.1)
        try:
            with socket.create_connection((host, port), timeout=0.2):
                return True
        except OSError:
            continue
    return False


def _aquaload_set_page_config(*args, **kwargs):
    """Keep the browser tab icon consistent across every AquaLoad page."""
    kwargs["page_icon"] = Image.open(PROJECT_DIR / "AquaLoad.png")
    return _ORIGINAL_SET_PAGE_CONFIG(*args, **kwargs)


# bootstrap.py is imported before page configuration throughout the app. Wrap
# Streamlit once so existing customer, staff, and public pages share the logo.
if not getattr(st, "_aquaload_logo_icon_enabled", False):
    st.set_page_config = _aquaload_set_page_config
    st._aquaload_logo_icon_enabled = True


def bootstrap_app():
    """Prepare Supabase PostgreSQL schema and fixed box templates without re-seeding demo data.

    Demo/reference data is seeded explicitly by `python setup_database.py` so
    Staff changes are not silently overwritten on every Streamlit rerun.
    """
    ensure_tracking_api()
    initialize_schema()
    ensure_box_templates()
