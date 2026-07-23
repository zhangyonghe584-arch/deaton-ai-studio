import json
import os
import shutil
import uuid
from datetime import datetime


DEFAULT_BRAND = {
    "name": "DEATON AUTO",
    "subtitle": "Professional Remote Vehicle Programming",
    "primary_color": "#111D30",
    "accent_color": "#22D3EE",
    "logo": "",
    "footer": "Worldwide Remote Programming",
    "font": "Microsoft YaHei"
}


class BrandService:
    """
    Deaton Auto Brand Manager

    管理：
    - config/brand.json
    - resources/branding/logo
    """

    def __init__(self, base_path=None):

        if base_path is None:
            base_path = os.path.dirname(
                os.path.dirname(__file__)
            )

        self.base_path = os.path.abspath(base_path)

        self.config_dir = os.path.join(
            self.base_path,
            "config"
        )

        self.brand_file = os.path.join(
            self.config_dir,
            "brand.json"
        )

        self.logo_dir = os.path.join(
            self.base_path,
            "resources",
            "branding",
            "logo"
        )

        os.makedirs(
            self.config_dir,
            exist_ok=True
        )

        os.makedirs(
            self.logo_dir,
            exist_ok=True
        )

        self.initialize()


    def initialize(self):
        if not os.path.exists(self.brand_file):
            self._write_profile(DEFAULT_BRAND.copy())

    def load_profile(self):
        self.initialize()
        with open(self.brand_file, "r", encoding="utf-8") as file:
            data = json.load(file)

        profile = DEFAULT_BRAND.copy()
        profile.update(data)
        return profile

    def save_profile(self, values):
        profile = self.load_profile()
        profile.update(values)
        self._write_profile(profile)
        return profile

    def _write_profile(self, profile):
        with open(self.brand_file, "w", encoding="utf-8") as file:
            json.dump(profile, file, ensure_ascii=False, indent=4)



    def import_logo(self, logo_path):

        if not os.path.isfile(
            logo_path
        ):
            return None


        ext = os.path.splitext(
            logo_path
        )[1].lower()


        if ext not in [
            ".png",
            ".jpg",
            ".jpeg",
            ".svg"
        ]:
            return None


        filename = (
            datetime.now()
            .strftime("%Y%m%d_%H%M%S")
            +
            "_"
            +
            uuid.uuid4().hex[:8]
            +
            ext
        )


        target = os.path.join(
            self.logo_dir,
            filename
        )


        shutil.copy2(
            logo_path,
            target
        )


        relative = os.path.relpath(
            target,
            self.base_path
        )


        self.save_profile(
            {
                "logo": relative
            }
        )


        return target



    def get_logo_path(self):

        brand = self.load_profile()

        logo = brand.get(
            "logo",
            ""
        )

        if not logo:
            return ""


        return os.path.join(
            self.base_path,
            logo.replace(
                "\\",
                os.sep
            )
        )



    def list_logos(self):

        if not os.path.exists(
            self.logo_dir
        ):
            return []


        return sorted(
            os.listdir(
                self.logo_dir
            )
        )