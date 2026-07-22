from engine.project_manager import ProjectManager


pm = ProjectManager()

path = pm.create_project(
    "BMW_G20"
)

print(path)