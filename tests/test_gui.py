"""Kiểm tra luồng xử lý của giao diện mà không cần màn hình."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from hybrid_crypto.gui import App


class Variable:
    def __init__(self, value=""):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class Table:
    def selection(self):
        return ("0",)

    def selection_set(self, value):
        pass


class HeadlessApp:
    key = App.key
    create_keys = App.create_keys
    signing_keys = App.signing_keys
    validate_output = App.validate_output
    seal_csv = App.seal_csv
    tamper = App.tamper
    new_version = App.new_version
    show_package = App.show_package

    def __init__(self, folder):
        self.key_dir = Variable(str(folder))
        self.csv_path = Variable(str(Path(__file__).resolve().parents[1] / "data/input/sample_cod.csv"))
        self.session_id = Variable("DS001")
        self.shop_id = Variable("SHOP001")
        self.fee, self.amount = Variable("75000"), Variable("225000")
        self.status, self.info = Variable(), Variable()
        self.table = Table()
        self.package = self.opened = self.edited = None
        self.saved = []

    def save_package(self, package):
        self.saved.append(package)
        return True

    def render(self, records, checks):
        self.displayed = records, checks


class GuiFlowTests(unittest.TestCase):
    def test_seal_edit_version(self):
        with tempfile.TemporaryDirectory() as folder:
            app = HeadlessApp(folder)
            app.create_keys()
            app.seal_csv()
            self.assertEqual(app.displayed[1], [True, True])
            app.tamper()
            self.assertEqual(app.displayed[1], [False, True])
            app.new_version()
            self.assertEqual(app.opened["chain"], "khop")
            self.assertEqual(app.opened["metadata"]["version"], 2)
            self.assertEqual(app.opened["records"][0]["shipping_fee"], 75000)
            self.assertEqual(len(app.saved), 2)
            self.assertEqual(app.saved[0]["metadata"]["version"], 1)

    def test_invalid_edit_clears_old_copy(self):
        with tempfile.TemporaryDirectory() as folder:
            app = HeadlessApp(folder)
            app.create_keys()
            app.seal_csv()
            app.tamper()
            app.amount.set("1")
            with self.assertRaises(ValueError):
                app.tamper()
            self.assertIsNone(app.edited)
            with self.assertRaises(ValueError):
                app.new_version()


if __name__ == "__main__":
    unittest.main()
