"""Giao diện desktop cho mô phỏng đối soát cục bộ."""
import copy
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from . import crypto, session, storage
from .cli import write_key
from .records import read_csv, validate


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Mô phỏng đối soát COD")
        self.geometry("1100x850")
        self.minsize(850, 650)
        self.key_dir = tk.StringVar()
        self.csv_path = tk.StringVar()
        self.session_id = tk.StringVar(value="DS001")
        self.shop_id = tk.StringVar(value="SHOP001")
        self.fee = tk.StringVar(value="75000")
        self.amount = tk.StringVar(value="225000")
        self.status = tk.StringVar(value="Bắt đầu: chọn một thư mục trống, rồi bấm ‘Tạo khóa mới’.")
        self.info = tk.StringVar(value="Chưa mở phiên nào.")
        self.package = self.opened = self.edited = None
        self.build()

    def build(self):
        outer = ttk.Frame(self, padding=16)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="Mô phỏng đối soát COD", font=("TkDefaultFont", 18, "bold")).pack(anchor="w")
        ttk.Label(outer, text="Thử xem hệ thống phát hiện một bản ghi bị sửa như thế nào.").pack(anchor="w", pady=(2, 6))
        guide = ttk.LabelFrame(outer, text="Bắt đầu tại đây", padding=8)
        guide.pack(fill="x", pady=(0, 6))
        ttk.Label(guide, text="① Tạo khóa và chọn dữ liệu mẫu   →   ② Chốt, lưu phiên gốc   →   ③ Sửa bản sao và kiểm tra", wraplength=950, justify="left").pack(anchor="w")
        ttk.Label(guide, text="Phiên gốc là bản đã xác nhận. Bản sao dùng để thử sửa và không làm thay đổi file gốc.", wraplength=950).pack(anchor="w", pady=(3, 0))

        setup = ttk.LabelFrame(outer, text="Bước 1 · Chuẩn bị khóa và dữ liệu", padding=10)
        setup.pack(fill="x", pady=4)
        setup.columnconfigure(1, weight=1)
        ttk.Label(setup, text="Thư mục khóa").grid(row=0, column=0, sticky="w", padx=(0, 8))
        ttk.Entry(setup, textvariable=self.key_dir).grid(row=0, column=1, sticky="ew")
        ttk.Button(setup, text="Chọn...", command=self.choose_keys).grid(row=0, column=2, padx=5)
        ttk.Button(setup, text="Tạo khóa mới", command=self.guard(self.create_keys)).grid(row=0, column=3)
        ttk.Label(setup, text="Tệp CSV").grid(row=1, column=0, sticky="w", pady=6)
        ttk.Entry(setup, textvariable=self.csv_path).grid(row=1, column=1, sticky="ew")
        ttk.Button(setup, text="Chọn...", command=self.choose_csv).grid(row=1, column=2, padx=5)
        ttk.Button(setup, text="Dùng CSV mẫu", command=self.use_sample).grid(row=1, column=3)
        ttk.Label(setup, text="Lần đầu: chọn thư mục trống và tạo khóa. Lần sau: chọn lại thư mục khóa cũ để mở phiên đã lưu.", wraplength=900).grid(row=3, column=1, columnspan=3, sticky="w", pady=(5, 0))
        ids = ttk.Frame(setup)
        ids.grid(row=2, column=1, sticky="w")
        ttk.Label(ids, text="Mã phiên").pack(side="left")
        ttk.Entry(ids, textvariable=self.session_id, width=16).pack(side="left", padx=(6, 18))
        ttk.Label(ids, text="Mã shop").pack(side="left")
        ttk.Entry(ids, textvariable=self.shop_id, width=16).pack(side="left", padx=6)

        actions = ttk.LabelFrame(outer, text="Bước 2 · Tạo hoặc mở phiên gốc", padding=10)
        actions.pack(fill="x", pady=4)
        ttk.Button(actions, text="Chốt CSV thành phiên mới", command=self.guard(self.seal_csv)).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Mở và xác minh phiên", command=self.guard(self.open_package)).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Đối chiếu phiên trước", command=self.guard(self.check_previous)).pack(side="left")
        ttk.Label(outer, text="Chốt = xác nhận dữ liệu, mã hóa và lưu file JSON. Mở = giải mã và so sánh với dữ liệu đã chốt.", wraplength=1000).pack(anchor="w", pady=(4, 0))
        feedback = ttk.LabelFrame(outer, text="Kết quả và việc cần làm tiếp", padding=8)
        feedback.pack(fill="x", pady=5)
        ttk.Label(feedback, textvariable=self.status, wraplength=1000, justify="left", font=("TkDefaultFont", 10, "bold")).pack(anchor="w")
        ttk.Label(feedback, textvariable=self.info, wraplength=1000, justify="left").pack(anchor="w", pady=(4, 0))

        frame = ttk.Frame(outer)
        frame.pack(fill="both", expand=True)
        columns = ("tracking", "cod", "fee", "amount", "result")
        self.table = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse", height=5)
        for col, title, width in [("tracking", "Vận đơn", 150), ("cod", "COD (đ)", 140), ("fee", "Phí (đ)", 140), ("amount", "Shop nhận (đ)", 150), ("result", "Merkle", 140)]:
            self.table.heading(col, text=title)
            self.table.column(col, width=width, anchor="w")
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=scrollbar.set)
        self.table.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        demo = ttk.LabelFrame(outer, text="Bước 3 · Thử sửa bản sao và xem kết quả", padding=10)
        demo.pack(fill="x", pady=8)
        ttk.Label(demo, text="Chọn VD001 trong bảng. Thử phí 75000 và shop nhận 225000, rồi bấm Kiểm tra bản sao.").grid(row=0, column=0, columnspan=5, sticky="w", pady=(0, 6))
        ttk.Label(demo, text="Phí mới").grid(row=1, column=0, sticky="w")
        ttk.Entry(demo, textvariable=self.fee, width=14).grid(row=1, column=1, padx=6)
        ttk.Label(demo, text="Shop nhận mới").grid(row=1, column=2, padx=(8, 0))
        ttk.Entry(demo, textvariable=self.amount, width=14).grid(row=1, column=3, padx=6)
        ttk.Button(demo, text="Kiểm tra bản sao", command=self.guard(self.tamper)).grid(row=1, column=4, padx=6)
        ttk.Button(demo, text="Chốt thành phiên bản mới", command=self.guard(self.new_version)).grid(row=2, column=4, padx=6, pady=(8, 0))
        ttk.Label(outer, text="Khớp = giống bản đã chốt  ·  Không khớp = nội dung khác bản đã chốt  ·  Số tiền nhập theo đồng, không có dấu chấm.", wraplength=1000).pack(anchor="w")

    def guard(self, func):
        def run():
            try:
                func()
            except Exception as exc:
                messagebox.showerror("Không thể thực hiện", str(exc) or type(exc).__name__, parent=self)
        return run

    def choose_keys(self):
        path = filedialog.askdirectory(title="Chọn thư mục chứa khóa", parent=self)
        if path:
            self.key_dir.set(path)

    def choose_csv(self):
        path = filedialog.askopenfilename(title="Chọn CSV", filetypes=[("CSV", "*.csv"), ("Tất cả", "*")], parent=self)
        if path:
            self.csv_path.set(path)

    def use_sample(self):
        path = Path(__file__).resolve().parents[2] / "data" / "input" / "sample_cod.csv"
        if not path.is_file():
            messagebox.showerror("Không tìm thấy dữ liệu mẫu", "Hãy chọn file CSV bằng nút Chọn...", parent=self)
            return
        self.csv_path.set(str(path))
        self.status.set("Đã chọn CSV mẫu. Nếu đã tạo khóa, bấm ‘Chốt CSV thành phiên mới’ để lưu phiên gốc.")

    def key(self, name, private=False):
        if not self.key_dir.get().strip():
            raise ValueError("Hãy chọn thư mục khóa trước.")
        data = (Path(self.key_dir.get()) / name).read_bytes()
        return crypto.load_private(data) if private else crypto.load_public(data)

    def create_keys(self):
        if not self.key_dir.get().strip():
            raise ValueError("Hãy chọn thư mục khóa trước.")
        folder = Path(self.key_dir.get())
        names = [folder / f"{name}_{kind}.pem" for name in ("issuer", "shop") for kind in ("private", "public")]
        if any(path.exists() for path in names):
            raise ValueError("Thư mục đã có file khóa. Hãy chọn thư mục mới.")
        for name in ("issuer", "shop"):
            private, public = crypto.generate_keypair()
            write_key(folder / f"{name}_private.pem", private, True)
            write_key(folder / f"{name}_public.pem", public, False)
        self.status.set("Đã tạo khóa. Tiếp theo bấm ‘Dùng CSV mẫu’, rồi chốt và lưu phiên gốc. Giữ lại thư mục khóa.")

    def signing_keys(self):
        private = self.key("issuer_private.pem", True)
        public = self.key("issuer_public.pem")
        crypto.verify(b"key-check", crypto.sign(b"key-check", private), public)
        return private, public

    def save_package(self, package):
        path = filedialog.asksaveasfilename(title="Lưu phiên (chọn tên file mới)", defaultextension=".json", filetypes=[("JSON", "*.json")], parent=self)
        if not path:
            return False
        storage.write_json(path, package)
        return True

    def seal_csv(self):
        if not self.csv_path.get().strip():
            raise ValueError("Hãy chọn file CSV.")
        private, public = self.signing_keys()
        package = session.seal(read_csv(self.csv_path.get()), self.session_id.get(), self.shop_id.get(), self.key("shop_public.pem"), private, issuer_public=public)
        self.validate_output(package)
        if self.save_package(package):
            self.show_package(package)
            self.status.set("Đã lưu phiên gốc. Chọn VD001 trong bảng, rồi bấm ‘Kiểm tra bản sao’ ở bước 3.")

    def validate_output(self, package):
        result = session.open_session(package, self.key("shop_private.pem", True), self.key("issuer_public.pem"))
        if not all(result["valid"]):
            raise ValueError("Khóa shop không khớp hoặc phiên không hợp lệ.")

    def open_package(self):
        path = filedialog.askopenfilename(title="Chọn phiên JSON", filetypes=[("JSON", "*.json")], parent=self)
        if path:
            self.show_package(storage.read_json(path))
            self.status.set("Đã mở phiên. Chữ ký đã được xác thực bằng khóa phát hành đã chọn.")

    def show_package(self, package, previous=None):
        opened = session.open_session(package, self.key("shop_private.pem", True), self.key("issuer_public.pem"), previous)
        self.package, self.opened, self.edited = package, opened, None
        meta = opened["metadata"]
        self.session_id.set(meta["session_id"])
        self.shop_id.set(meta["shop_id"])
        self.info.set(f"Phiên {meta['session_id']} · Shop {meta['shop_id']} · Phiên bản {meta['version']} · Chuỗi: {opened['chain']}\nMerkle root: {meta['merkle_root']}")
        self.render(opened["records"], opened["valid"])

    def render(self, records, checks):
        self.table.delete(*self.table.get_children())
        for i, (record, valid) in enumerate(zip(records, checks)):
            if record is None:
                values = ("Không giải mã được", "", "", "", "Không khớp")
            else:
                values = (record.get("tracking_id", "?"), record.get("cod", "?"), record.get("shipping_fee", "?"), record.get("shop_amount", "?"), "Khớp" if valid else "Không khớp")
            self.table.insert("", "end", iid=str(i), values=values)

    def check_previous(self):
        if self.package is None:
            raise ValueError("Hãy mở phiên trước.")
        path = filedialog.askopenfilename(title="Chọn phiên bản ngay trước", filetypes=[("JSON", "*.json")], parent=self)
        if path:
            self.show_package(self.package, storage.read_json(path))
            self.status.set("Đã đối chiếu liên kết với phiên trước.")

    def tamper(self):
        self.edited = None
        if self.opened is None or not all(self.opened["valid"]):
            raise ValueError("Hãy mở một phiên có tất cả bản ghi hợp lệ.")
        selected = self.table.selection()
        if not selected:
            raise ValueError("Hãy chọn bản ghi trong bảng.")
        if not self.fee.get().isascii() or not self.fee.get().isdigit() or not self.amount.get().isascii() or not self.amount.get().isdigit():
            raise ValueError("Số tiền phải là số nguyên không âm.")
        index = int(selected[0])
        edited = copy.deepcopy(self.opened["records"])
        edited[index]["shipping_fee"] = int(self.fee.get())
        edited[index]["shop_amount"] = int(self.amount.get())
        validate(edited)
        checks = [session.verify_record(record, self.opened["metadata"], i, self.package["records"][i]["proof"]) for i, record in enumerate(edited)]
        self.edited = edited
        self.render(edited, checks)
        self.table.selection_set(str(index))
        self.status.set("Phép tính tiền đúng. " + ("Bản sao vẫn giống phiên gốc." if checks[index] else "Bản sao khác phiên gốc: Merkle phát hiện bản ghi đã bị sửa. File gốc vẫn giữ nguyên."))

    def new_version(self):
        if self.edited is None:
            raise ValueError("Hãy kiểm tra bản sao trước khi tạo phiên bản mới.")
        private, public = self.signing_keys()
        meta = self.opened["metadata"]
        package = session.seal(self.edited, meta["session_id"], meta["shop_id"], self.key("shop_public.pem"), private, self.package, public)
        self.validate_output(package)
        if self.save_package(package):
            previous = self.package
            self.show_package(package, previous)
            self.status.set("Đã lưu phiên bản mới và kiểm tra liên kết. File phiên gốc vẫn được giữ nguyên.")


def main():
    App().mainloop()


if __name__ == "__main__":
    main()
