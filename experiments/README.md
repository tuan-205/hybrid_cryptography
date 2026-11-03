# Kế hoạch thực nghiệm trên máy cá nhân

Chưa có chương trình thực nghiệm; các bước sau là kế hoạch triển khai, không phải lệnh đã chạy.

1. Tạo dữ liệu tổng hợp có thể tái tạo; lưu cấu hình, kích thước khối và dấu vết sinh dữ liệu. Không đưa dữ liệu thật hoặc khóa riêng vào Git.
2. Mã hóa và giải mã, so sánh dữ liệu khôi phục; tạo và xác minh Merkle proof với gốc được lưu đáng tin cậy.
3. Kiểm tra 10 khối nguyên vẹn; sửa khối thứ 6 và ghi rõ kết quả kiểm tra từng khối, cả trước và sau khi sửa. Thử cả thay ciphertext, khóa bọc và proof.
4. Đo riêng tạo khóa, mã hóa, giải mã và xác minh với 1–10 khối. Ghi số lần lặp, warm-up, thời gian từng lần, thống kê, hệ điều hành, CPU, phiên bản Python và thư viện. Chỉ so sánh Twofish+ElGamal khi đã có triển khai tương đương và thống nhất điều kiện đo.
5. Lưu cấu hình trong `configs/`, số liệu trong `../results/raw/`, biểu đồ trong `../results/figures/`. Báo cáo các khác biệt với Bảng 2 thay vì giả định số liệu phải giống nhau.
