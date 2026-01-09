# PTIT AntiPhishing

PTIT AntiPhishing là một ứng dụng phát hiện trang web lừa đảo theo thời gian thực bằng cách phân tích nội dung trang web và sử dụng mô hình MobileBERT, được triển khai dưới dạng tiện ích mở rộng Chrome và hoàn toàn ở phía người dùng.

Repo này bao gồm:
- **Tập dữ liệu:** Tập dữ liệu bao gồm tập dữ liệu dùng để huấn luyện và tập dữ liệu dùng để dự đoán. Các tập dữ liệu đều được chia làm 2 phần là các mẫu trang web lừa đảo và các mẫu trang web hợp pháp, có các mẫu trang web gốc là các file HTML và các mẫu trang web sau khi đã được xử lý một cách có cấu trúc.
- **Mô hình MobileBERT và Server:** Mô hình MobileBERT sau khi đã được huấn luyện cùng với các file Python sử dụng trong quá trình xử lý tập dữ liệu, huấn luyện và đánh giá mô hình. File **`app.py`** là server sẽ luôn chạy như một dịch vụ nền trong hệ điều hành Linux để gọi mô hình đã được huấn luyện và đánh giá trang web là hợp pháp hay lừa đảo. Mô hình MobileBERT đã được huấn luyện và server được đóng gói trong file **`antiphishing_1.0.deb`** để cài đặt trên các máy Linux khác nhau.
- **Tiện ích mở rộng Chrome:** Toàn bộ phần giao diện và xử lý logic của tiện ích PTIT AntiPhishing cùng với file **`extension.crx`** để cài đặt.

## Tập dữ liệu

Do kích thước quá lớn nên tập dữ liệu được lưu trữ ở trên HuggingFace [(HuggingFace Dataset Link)](https://huggingface.co/datasets/vumanh2003/dataset-datn/tree/main).

## Hướng dẫn cài đặt ứng dụng

### Bước 1: Cài đặt dịch vụ ở phía người dùng

Tải xuống hoặc clone repo này về một máy Linux (Ubuntu 22.04 LTS / Ubuntu 24.04 LTS). Trong Terminal sử dụng câu lệnh sau:
    
    sudo dpkg -i antiphishing_1.0.deb

**Chú ý:** Các gói python3 (phiên bản 3.10) và python3-pip cần được cài đặt rồi, sẽ mất một vài phút để cài đặt xong file **`antiphishing_1.0.deb`**.

Sau khi cài đặt xong, server sẽ luôn luôn chạy như một dịch vụ nền trong hệ điều hành Linux. Để kiểm tra trạng thái của server, sử dụng câu lệnh sau:

    sudo systemctl status antiphishing.service

**Chú ý:** Có thể sẽ gặp lỗi không import được thư viện chứa mô hình MobileBERT. Điều này xảy ra là do pip3 sẽ tự động cài gói transformers mới nhất trong khi thư viện chứa mô hình MobileBERT chỉ có ở các gói cũ. Để xử lý lỗi này, hãy gỡ cài đặt gói transformers hiện có và cài đặt lại gói transformers 4.44.0 bằng các câu lệnh sau:

    sudo pip uninstall transformers
    sudo pip install transformers==4.44.0

Sau đó hãy khởi động lại dịch vụ **`antiphishing.service`** và kiểm tra lại trạng thái của dịch vụ bằng các câu lệnh sau:

    sudo systemctl restart antiphishing.service
    sudo systemctl status antiphishing.service

### Bước 2: Cài đặt tiện ích mở rộng

Mở trình duyệt Chromium trên Linux:

1. Click vào dấu ba chấm ở phía trên cùng bên phải trình duyệt -> Chọn `Extensions` -> Chọn `Manage Extensions` -> Bật chế độ cho nhà phát triển `Developer mode`.
2. Kéo và thả file **`extension.crx`** vào trong cửa sổ trình duyệt.
