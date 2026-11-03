# Mô phỏng đối soát COD

Mô phỏng bên phát hành chốt CSV, mã hóa từng bản ghi cho shop và xác minh bản ghi bằng Merkle proof. Đây là ứng dụng nghiên cứu dựa trên bài báo, không phải hệ thống GHN.

## Cài đặt và chạy demo

Cần Python 3.10 trở lên. Tại thư mục dự án:

```bash
python -m venv .venv
# macOS/Linux: source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e .
python experiments/tamper_demo.py
python -m unittest discover -s tests -v
```

Demo dùng dữ liệu giả lập, sửa phí VD001 từ 25.000 thành 75.000 đồng và tiền nhận từ 275.000 thành 225.000 đồng. Phép tính vẫn đúng nhưng proof không khớp root gốc; sau đó demo tạo phiên bản mới.

## Chạy từng bước

```bash
python -m hybrid_crypto keys keys
python -m hybrid_crypto seal data/input/sample_cod.csv results/raw/ds001-v1.json --session DS001 --shop SHOP001 --issuer-private keys/issuer_private.pem --issuer-public keys/issuer_public.pem --shop-public keys/shop_public.pem
python -m hybrid_crypto open results/raw/ds001-v1.json --shop-private keys/shop_private.pem --issuer-public keys/issuer_public.pem
```

Tạo phiên bản tiếp theo bằng lệnh `seal` tương tự, dùng CSV đã sửa, tên file đầu ra mới và thêm `--previous results/raw/ds001-v1.json`. Khi mở phiên bản mới, thêm `--previous` để đối chiếu liên kết. File đầu ra không được ghi đè. Dùng `python -m hybrid_crypto --help` để xem các lệnh.

CSV gồm các cột `tracking_id,cod,shipping_fee,shop_amount`; số tiền là số nguyên đồng. Giữ bí mật khóa riêng và xác nhận khóa công khai của bên phát hành qua kênh tin cậy. Mã chỉ phục vụ mô phỏng; xem [thiết kế](docs/design.md) để biết giới hạn.
