import os


OPTION_FIELDS = (
    "customer_region",
    "brand",
    "model",
    "year",
    "engine_model",
    "fault_category",
    "service_type",
    "programming_type",
    "equipment_used",
    "repair_result",
)


class CaseOptionService:
    """Loads editable case-form suggestions from one-value-per-line text files."""

    def __init__(self, options_directory="config/options"):
        self.options_directory = options_directory

    def list_options(self, field):
        if field not in OPTION_FIELDS:
            return []

        path = os.path.join(self.options_directory, f"{field}.txt")
        if not os.path.isfile(path):
            return []

        with open(path, encoding="utf-8") as file:
            values = [line.strip() for line in file]
        return list(dict.fromkeys(value for value in values if value and not value.startswith("#")))

    def options_directory_path(self):
        return os.path.abspath(self.options_directory)
