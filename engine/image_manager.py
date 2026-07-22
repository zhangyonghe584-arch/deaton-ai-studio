import os
import shutil


CATEGORY_MAP = {

    "01 车辆外观": "01_vehicle",

    "02 故障现象": "02_fault",

    "03 诊断过程": "03_diagnosis",

    "04 编程过程": "04_programming",

    "05 完成结果": "05_result",

    "06 技术资料": "06_technical"

}



class ImageManager:


    def __init__(self, project_path):

        self.project_path = project_path



    def save_image(self, image_path, category_name):

        if category_name not in CATEGORY_MAP:

            return None


        folder = CATEGORY_MAP[category_name]


        target_dir = os.path.join(

            self.project_path,

            "images",

            folder

        )


        os.makedirs(

            target_dir,

            exist_ok=True

        )


        filename = os.path.basename(
            image_path
        )


        target = os.path.join(

            target_dir,

            filename

        )


        # 复制图片到项目目录

        shutil.copy2(

            image_path,

            target

        )


        print(
            "保存图片:",
            target
        )


        return target