# Thiết kế dự kiến và giới hạn tái lập

## Ánh xạ bài báo

- Mục 3.1–3.2: AES mã hóa từng khối; RSA bảo vệ khóa AES. Mã dự kiến đặt trong `src/hybrid_crypto/crypto/`.
- Mục 3.3–3.4 và 4: băm khối, tạo khóa kế tiếp, cây Merkle, gốc và bằng chứng. Mã dự kiến đặt trong `src/hybrid_crypto/integrity/`; quy trình tổng hợp trong `pipeline/`.
- Mục 5.1: kiểm tra dữ liệu hợp lệ và sửa khối thứ 6 trong 10 khối. Mục 5.2, Bảng 2: so sánh thời gian AES+RSA với Twofish+ElGamal cho 1–10 khối. Thực nghiệm dự kiến đặt trong `experiments/`.

## Các quyết định còn thiếu

Bài báo không xác định đầy đủ chế độ AES, padding RSA, hàm băm, định dạng dữ liệu, kích thước khối, quy tắc nút lẻ của cây Merkle, môi trường đo và quy trình đo chi tiết. Không suy diễn các giá trị này là thông số gốc; khi triển khai cần ghi rõ giả định, phiên bản thư viện và cấu hình từng lần chạy. Dữ liệu dẫn xuất của tác giả được cung cấp theo yêu cầu, nên phải dùng dữ liệu tự tạo hoặc liên hệ tác giả để tái lập.

Mã giả mục 4 tạo khóa AES tiếp theo từ hash của dữ liệu và có đoạn văn nói mã hóa bằng khóa RSA riêng, trong khi mã giả dùng khóa công khai. Cần tách bản mô phỏng nghiên cứu khỏi thiết kế an toàn: dữ liệu có thể đoán được không phải nguồn khóa bí mật, mã hóa khóa AES phải dùng khóa công khai của bên nhận, và gốc Merkle cần được xác thực qua kênh tin cậy. Mô phỏng đúng mã giả không chứng minh an toàn cho ứng dụng thực tế.

Hiệu ứng các khối sau khối 6 bị đánh dấu không hợp lệ phải được kiểm tra theo quy tắc chuỗi đã triển khai; Merkle proof riêng của một lá không tự chứng minh mọi lá sau đều sai. Hai thuật toán Twofish+ElGamal là hướng so sánh bổ sung và cần được triển khai, kiểm chứng riêng trước khi so sánh.
