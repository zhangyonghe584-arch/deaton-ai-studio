import os
import tempfile
import unittest

from engine.case_option_service import CaseOptionService


class CaseOptionServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.options_dir = os.path.join(self.temp_dir.name, "options")
        os.makedirs(self.options_dir)
        self.service = CaseOptionService(self.options_dir)

    def test_lists_trimmed_non_comment_values_from_text_file(self):
        with open(
            os.path.join(self.options_dir, "fault_category.txt"),
            "w",
            encoding="utf-8",
        ) as file:
            file.write("# 每行一个选项\n\n发动机故障\n 编程升级 \n发动机故障\n")

        self.assertEqual(
            self.service.list_options("fault_category"),
            ["发动机故障", "编程升级"],
        )

    def test_returns_empty_list_when_option_file_is_missing(self):
        self.assertEqual(self.service.list_options("service_type"), [])


if __name__ == "__main__":
    unittest.main()
