import os


class FileManager:
    @staticmethod
    def get_project_path(self, project_code: str) -> str:
        return os.path.join("/mnt", project_code)

    @staticmethod
    def generate_shot_path(project_path: str, division: str, ep: str, seq: str, shot: str) -> str:
        return os.path.join(project_path, division, f"ep{ep}", f"ep{ep}_sq{seq}", f"ep{ep}_sq{seq}_sh{shot}")