from django.contrib.staticfiles.storage import ManifestStaticFilesStorage


def _is_excluded(name: str) -> bool:
    return name.startswith("bundler/") or name.endswith(".map")


class SelectiveManifestStaticFilesStorage(ManifestStaticFilesStorage):
    def hashed_name(self, name, content=None, filename=None):
        if _is_excluded(name):
            return name
        else:
            return super().hashed_name(name, content, filename)
