"""Giao diện desktop cho mô phỏng đối soát cục bộ."""
import copy
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, font

from . import crypto, session, storage
from .cli import write_key
from .records import read_csv, validate


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Mô phỏng đối soát COD")
        self.geometry("1080x720")
        self.minsize(920, 650)
        self.key_dir = tk.StringVar()
        self.csv_path = tk.StringVar()
        self.session_id = tk.StringVar(value="DS001")
        self.shop_id = tk.StringVar(value="SHOP001")
        self.fee = tk.StringVar(value="75000")
        self.amount = tk.StringVar(value="225000")
        self.status = tk.StringVar(value="Chọn thư mục khóa và dữ liệu CSV.")
        self.info = tk.StringVar(value="Chưa mở phiên nào.")
        self.package = self.opened = self.edited = None
        self.build()

    def build(self):
        for name in ("TkDefaultFont", "TkTextFont", "TkMenuFont"):
            font.nametofont(name).configure(size=13)
        style = ttk.Style(self)
        style.configure("TButton", padding=(10, 7))
        style.configure("TEntry", padding=5)
        style.configure("Treeview", font=font.nametofont("TkDefaultFont"), rowheight=36)
        style.configure("Treeview.Heading", font=(font.nametofont("TkDefaultFont").actual("family"), 13, "bold"))
        outer = ttk.Frame(self, padding=20)
        outer.pack(fill="both", expand=True)
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(4, weight=1)

        header = ttk.Frame(outer)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        ttk.Label(header, text="Đối soát COD", font=(font.nametofont("TkDefaultFont").actual("family"), 24, "bold")).pack(side="left")
        ttk.Button(header, text="Trợ giúp", command=self.help).pack(side="right")

        setup = ttk.Frame(outer)
        setup.grid(row=1, column=0, sticky="ew")
        setup.columnconfigure(1, weight=1)
        for row, label, variable, choose, extra, callback in (
                (0, "Thư mục khóa", self.key_dir, self.choose_keys, "Tạo khóa", self.guard(self.create_keys)),
                (1, "Dữ liệu CSV", self.csv_path, self.choose_csv, "Dùng mẫu", self.use_sample)):
            ttk.Label(setup, text=label).grid(row=row, column=0, sticky="w", padx=(0, 12))
            ttk.Entry(setup, textvariable=variable).grid(row=row, column=1, sticky="ew", pady=4)
            ttk.Button(setup, text="Chọn…", command=choose).grid(row=row, column=2, padx=8)
            ttk.Button(setup, text=extra, command=callback, width=10).grid(row=row, column=3)
        ids = ttk.Frame(setup)
        ids.grid(row=2, column=1, columnspan=3, sticky="w", pady=6)
        for label, variable in (("Phiên", self.session_id), ("Shop", self.shop_id)):
            ttk.Label(ids, text=label).pack(side="left", padx=(0, 8))
            ttk.Entry(ids, textvariable=variable, width=14).pack(side="left", padx=(0, 20))

        actions = ttk.Frame(outer)
        actions.grid(row=2, column=0, sticky="ew", pady=10)
        for label, callback in (("Chốt & lưu", self.seal_csv), ("Mở phiên", self.open_package), ("Đối chiếu phiên trước", self.check_previous)):
            ttk.Button(actions, text=label, command=self.guard(callback)).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Chi tiết", command=self.details).pack(side="right")
        ttk.Label(outer, textvariable=self.info).grid(row=3, column=0, sticky="w", pady=(0, 8))

        frame = ttk.Frame(outer)
        frame.grid(row=4, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        columns = ("tracking", "cod", "fee", "amount", "result")
        self.table = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse", height=5)
        for col, title in zip(columns, ("Vận đơn", "COD (đ)", "Phí (đ)", "Shop nhận (đ)", "Kết quả")):
            self.table.heading(col, text=title)
            self.table.column(col, width=155, minwidth=110, anchor="w" if col in ("tracking", "result") else "e")
        self.table.tag_configure("valid", foreground="#166534")
        self.table.tag_configure("invalid", foreground="#b91c1c")
        self.table.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.table.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        horizontal = ttk.Scrollbar(frame, orient="horizontal", command=self.table.xview)
        horizontal.grid(row=1, column=0, sticky="ew")
        self.table.configure(yscrollcommand=scrollbar.set, xscrollcommand=horizontal.set)

        demo = ttk.Frame(outer)
        demo.grid(row=5, column=0, sticky="ew", pady=(14, 8))
        ttk.Label(demo, text="Sửa bản sao", font=(font.nametofont("TkDefaultFont").actual("family"), 13, "bold")).grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 6))
        for col, label, variable in ((0, "Phí mới (đ)", self.fee), (2, "Shop nhận (đ)", self.amount)):
            ttk.Label(demo, text=label).grid(row=1, column=col, padx=(0, 8))
            ttk.Entry(demo, textvariable=variable, width=12).grid(row=1, column=col+1, padx=(0, 16))
        ttk.Button(demo, text="Kiểm tra", command=self.guard(self.tamper)).grid(row=1, column=4)
        ttk.Button(demo, text="Lưu phiên bản mới", command=self.guard(self.new_version)).grid(row=2, column=4, pady=(8, 0))
        status = ttk.Label(outer, textvariable=self.status, wraplength=900, foreground="#174775")
        status.grid(row=6, column=0, sticky="ew")
        outer.bind("<Configure>", lambda event: status.configure(wraplength=max(300, event.width - 40)))

    def help(self):
        messagebox.showinfo("Cách dùng", "Chọn thư mục trống → Tạo khóa → Dùng mẫu → Chốt & lưu.\n\n"
                            "Chọn VD001, nhập phí 75000 và tiền nhận 225000, rồi Kiểm tra.\n"
                            "Không khớp nghĩa là bản sao đã khác dữ liệu gốc.\n\n"
                            "Lưu phiên bản mới để ghi nhận thay đổi hợp lệ. Giữ file cũ và thư mục khóa để mở lại.", parent=self)

    def details(self):
        if self.opened is None:
            messagebox.showinfo("Chi tiết", "Chưa mở phiên.", parent=self)
            return
        meta = self.opened["metadata"]
        chain = {"khop": "Khớp", "khong co phien truoc": "Phiên đầu tiên", "chua doi chieu phien truoc": "Chưa đối chiếu phiên trước"}.get(self.opened["chain"], self.opened["chain"])
        messagebox.showinfo("Chi tiết phiên", f"Liên kết: {chain}\n\nMerkle root:\n{meta['merkle_root']}", parent=self)

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
        self.status.set("Đã chọn mẫu. Bấm Chốt & lưu khi đã có khóa.")

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
        self.status.set("Đã tạo khóa. Chọn CSV hoặc bấm Dùng mẫu.")

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
            self.status.set("Đã lưu. Chọn một dòng để thử sửa bản sao.")

    def validate_output(self, package):
        result = session.open_session(package, self.key("shop_private.pem", True), self.key("issuer_public.pem"))
        if not all(result["valid"]):
            raise ValueError("Khóa shop không khớp hoặc phiên không hợp lệ.")

    def open_package(self):
        path = filedialog.askopenfilename(title="Chọn phiên JSON", filetypes=[("JSON", "*.json")], parent=self)
        if path:
            self.show_package(storage.read_json(path))
            self.status.set("Đã mở. Chữ ký hợp lệ; xem kết quả từng dòng.")

    def show_package(self, package, previous=None):
        opened = session.open_session(package, self.key("shop_private.pem", True), self.key("issuer_public.pem"), previous)
        self.package, self.opened, self.edited = package, opened, None
        meta = opened["metadata"]
        self.session_id.set(meta["session_id"])
        self.shop_id.set(meta["shop_id"])
        self.info.set(f"{meta['session_id']} · {meta['shop_id']} · Phiên bản {meta['version']}")
        self.render(opened["records"], opened["valid"])

    def render(self, records, checks):
        self.table.delete(*self.table.get_children())
        for i, (record, valid) in enumerate(zip(records, checks)):
            if record is None:
                values = ("Không giải mã được", "", "", "", "Không khớp")
            else:
                values = (record.get("tracking_id", "?"), record.get("cod", "?"), record.get("shipping_fee", "?"), record.get("shop_amount", "?"), "Khớp" if valid else "Không khớp")
            self.table.insert("", "end", iid=str(i), values=values, tags=("valid" if valid else "invalid",))

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
        self.status.set("Phép tính tiền đúng. " + ("Bản sao vẫn giống phiên gốc." if checks[index] else "Bản sao không khớp; file gốc giữ nguyên."))

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
            self.status.set("Đã lưu bản mới. Liên kết khớp; file cũ giữ nguyên.")


def main():
    App().mainloop()


if __name__ == "__main__":
    main()
