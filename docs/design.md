# Thiết kế mô phỏng

Mỗi dòng CSV là một bản ghi. Dữ liệu được chuẩn hóa bằng JSON UTF-8 với thứ tự khóa cố định; hash lá bao gồm nội dung, mã phiên, mã shop, phiên bản và vị trí. Cây Merkle dùng SHA-256, tiền tố phân biệt lá/nút và nhân đôi nút cuối khi tầng có số nút lẻ.

Mỗi bản ghi dùng khóa AES-256-GCM ngẫu nhiên và nonce riêng; khóa AES được bọc bằng RSA-OAEP SHA-256 của shop. Bên phát hành ký thông tin phiên bằng RSA-PSS SHA-256, gồm root và hash thông tin đã ký của phiên bản trước. Bên nhận cần khóa công khai phát hành đáng tin cậy. Proof kiểm tra từng bản ghi sau giải mã với root đã xác thực.

Đây là điều chỉnh từ mã giả trong Fauzi và cộng sự, DOI [10.11591/ijece.v15i6.pp5679-5689](https://doi.org/10.11591/ijece.v15i6.pp5679-5689): khóa AES ngẫu nhiên, chuỗi liên kết phiên bản thay vì dẫn xuất khóa từ dữ liệu. Không khẳng định tái lập phép đo trong bài báo.

Liên kết chỉ được đối chiếu với phiên trước khi cung cấp `--previous`; việc xác định phiên bản mới nhất và giữ mốc đáng tin cậy là trách nhiệm người dùng. Chữ ký không chứng minh khoản phí đúng trước khi chốt. Khóa demo lưu không mã hóa và chỉ dùng cục bộ với dữ liệu giả lập.
