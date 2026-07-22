import json
import os
import tempfile


DEFAULT_BRAND = {
    "name": "DEATON AUTO",
    "subtitle": "AUTOMOTIVE CASE STUDIO",
    "primary_color": "#111D30",
    "accent_color": "#22D3EE",
}


class BrandService:
    """Stores the reusable publication identity outside individual case records."""

    def __init__(self, config_directory="config"):
        self.config_directory = config_directory
        self.profile_path = os.path.join(config_directory, "brand.json")

    def load_profile(self):
        profile = DEFAULT_BRAND.copy()
        if not os.path.isfile(self.profile_path):
            return profile

        with open(self.profile_path, encoding="utf-8") as file:
            stored_profile = json.load(file)
        for field in DEFAULT_BRAND:
            if field in stored_profile:
                profile[field] = stored_profile[field]
        return profile

    def save_profile(self, values):
        profile = self.load_profile()
        for field in ("name", "subtitle"):
            if field in values:
                profile[field] = str(values[field]).strip()
        for field in ("primary_color", "accent_color"):
            if field in values:
                profile[field] = self._normalize_color(values[field])

        os.makedirs(self.config_directory, exist_ok=True)
        descriptor, temporary_path = tempfile.mkstemp(
            dir=self.config_directory,
            prefix="brand-",
            suffix=".json",
        )
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as file:
                json.dump(profile, file, ensure_ascii=False, indent=4)
                file.flush()
                os.fsync(file.fileno())
            os.replace(temporary_path, self.profile_path)
        except Exception:
            if os.path.exists(temporary_path):
                os.unlink(temporary_path)
            raise
        return profile

    @staticmethod
    def _normalize_color(value):
        color = str(value).strip().upper()
        if len(color) == 7 and color.startswith("#") and all(
            character in "0123456789ABCDEF" for character in color[1:]
        ):
            return color
        raise ValueError("颜色必须是 #RRGGBB 格式")
