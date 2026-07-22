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
    "footer": "Worldwide Remote Programming"
}


class BrandService:
    """
    Deaton Auto Brand Manager

    管理：
    - brand.json
    - Logo资源
    - 品牌配置
    """


    def __init__(self, base_path="."):

        self.base_path = base_path

        self.config_dir = os.path.join(
            base_path,
            "config"
        )

        self.brand_file = os.path.join(
            self.config_dir,
            "brand.json"
        )


        self.logo_dir = os.path.join(
            base_path,
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

        """
        第一次运行自动创建品牌配置
        """

        if not os.path.exists(
            self.brand_file
        ):

            self.save_profile(
                DEFAULT_BRAND
            )



    def load_profile(self):

        if not os.path.exists(
            self.brand_file
        ):

            self.initialize()


        with open(
            self.brand_file,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)



    def save_profile(
        self,
        values
    ):


        profile = DEFAULT_BRAND.copy()


        if os.path.exists(
            self.brand_file
        ):

            profile.update(
                self.load_profile()
            )


        profile.update(
            values
        )


        with open(
            self.brand_file,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                profile,
                f,
                ensure_ascii=False,
                indent=4
            )


        return profile



    def import_logo(
        self,
        logo_path
    ):


        if not os.path.exists(
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
            uuid.uuid4().hex[:6]
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


        profile = self.load_profile()


        profile["logo"] = os.path.relpath(
            target,
            self.base_path
        )


        self.save_profile(
            profile
        )


        return target



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