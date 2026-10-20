import os
import platform

import django

from cantusdata.metrics.definitions import BUILD_INFO


def build_labels() -> dict[str, str]:
    # CANTUS_GIT_SHA is baked into the image by CI (app/Dockerfile, GIT_SHA).
    return {
        "git_sha": os.environ.get("CANTUS_GIT_SHA") or "unknown",
        "django": django.get_version(),
        "python": platform.python_version(),
    }


def publish_build_info() -> None:
    BUILD_INFO.labels(**build_labels()).set(1)
