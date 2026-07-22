import json
import os
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
        suffix = 2
        while os.path.exists(path):
            path = os.path.join(BASE_DIR, f"{project_name}_{suffix}")
            suffix += 1
        project_name = os.path.basename(path)

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
            "schema_version": 1,
            "project_name": project_name,
            "created": datetime.now().isoformat(),
            "vehicle": "",
            "fault": "",
            "service": "",
            "images": {},
            "videos": [],
            "case_info": {},
            "assets": [],
            "exports": []
        }

        with open(
            os.path.join(path, "project.json"),
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                info,
                file,
                ensure_ascii=False,
                indent=4
            )

        return path


    def create_new_case(self):

        return self.create_project(
            "New_Case"
        )
