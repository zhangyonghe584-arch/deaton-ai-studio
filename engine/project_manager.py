import os
import json
from datetime import datetime


BASE_DIR = "projects"


class ProjectManager:

    def __init__(self):

        if not os.path.exists(BASE_DIR):
            os.makedirs(BASE_DIR)



    def create_project(self, name):

        date = datetime.now().strftime("%Y%m%d")

        project_name = f"{date}_{name}"

        path = os.path.join(
            BASE_DIR,
            project_name
        )

    def create_new_case(self):

        return self.create_project(
            "New_Case"
        )    


        folders = [

            "images/01_vehicle",
            "images/02_fault",
            "images/03_diagnosis",
            "images/04_programming",
            "images/05_result",
            "images/06_technical",

            "videos",

            "ai",

            "output"

        ]


        for folder in folders:

            os.makedirs(
                os.path.join(path, folder),
                exist_ok=True
            )


        info = {

            "project_name": project_name,

            "created": datetime.now().isoformat(),

            "vehicle": "",

            "fault": "",

            "service": "",

            "images": {},

            "videos": []

        }


        with open(
            os.path.join(path,"project.json"),
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                info,
                f,
                ensure_ascii=False,
                indent=4
            )


        return path