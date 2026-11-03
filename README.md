# Thực nghiệm mật mã lai AES–RSA

Bộ khung dự án nghiên cứu dựa trên Fauzi, Farikhin và Jie, “Enhancing system integrity with Merkle tree: efficient hybrid cryptography using RSA and AES in hash chain systems”, IJECE 15(6), 2025, tr. 5679–5689, DOI [10.11591/ijece.v15i6.pp5679-5689](https://doi.org/10.11591/ijece.v15i6.pp5679-5689).

**Trạng thái:** mới có cấu trúc và kế hoạch thực nghiệm; chưa có mã mã hóa, chương trình chạy, dữ liệu hay kết quả. Chưa thể chạy lại các phép đo của bài báo. Không cần cài thư viện ở giai đoạn này. Python là lựa chọn đề xuất cho các bước triển khai tiếp theo, phù hợp chạy trên máy cá nhân.

```text
src/hybrid_crypto/
  crypto/       AES, RSA và quản lý khóa dự kiến
  integrity/    chuỗi băm, cây Merkle và bằng chứng dự kiến
  pipeline/     ghép khối, mã hóa, giải mã và xác minh dự kiến
experiments/
  configs/      cấu hình cho các lượt thực nghiệm dự kiến
  README.md     kịch bản và cách ghi nhận kết quả
data/
  input/        dữ liệu đầu vào do người dùng cung cấp
  generated/    dữ liệu tổng hợp được tạo cục bộ
results/
  raw/          số liệu đo cục bộ
  figures/      biểu đồ cục bộ
tests/
  unit/         kiểm thử từng thành phần dự kiến
  integration/  kiểm thử toàn bộ quy trình dự kiến
 docs/          thiết kế, giả định và giới hạn tái lập
```

Các thư mục chưa có mã được giữ trong Git bằng tệp `.gitkeep`. Xem [kế hoạch thực nghiệm](experiments/README.md) và [ghi chú thiết kế](docs/design.md) trước khi triển khai. Dữ liệu, kết quả và khóa tạo cục bộ được loại khỏi Git bằng `.gitignore`.
