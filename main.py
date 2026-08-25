"""Documentum Connector entrypoint."""
from __future__ import annotations

import handlers_connection  # noqa: F401
import handlers_documents  # noqa: F401
import handlers_lifecycle  # noqa: F401
import handlers_objects  # noqa: F401
import handlers_permissions  # noqa: F401
import handlers_search  # noqa: F401
import handlers_versions  # noqa: F401
import panels  # noqa: F401
import panels_center  # noqa: F401
import panels_settings  # noqa: F401
from app import ext

extension = ext
