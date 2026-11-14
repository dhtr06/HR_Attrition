# TalentPulse AI – Nền tảng Phân tích Nhân sự & Dự báo Nguy cơ Nghỉ việc (v2.0)

Hệ thống quản trị và phân tích dữ liệu nhân sự (People Analytics) tích hợp Trí tuệ Nhân tạo (Machine Learning) toàn diện, giao diện Web SaaS hiện đại, chuyên nghiệp, hỗ trợ ra quyết định giữ chân nhân tài và tối ưu hóa môi trường làm việc.

## Bài toán và phạm vi

- **Mục tiêu:** hỗ trợ HR nhận diện sớm các trường hợp có dấu hiệu nghỉ việc để cân nhắc trao đổi và hỗ trợ phù hợp; hệ thống không đưa ra quyết định nhân sự thay con người.
- **Nhãn huấn luyện:** `Attrition` (`Yes` = nghỉ việc, `No` = không nghỉ việc) trong bộ dữ liệu dùng cho bài tập.
- **Đầu vào mô hình:** tuổi, thu nhập tháng, thâm niên, làm thêm giờ, mức hài lòng, cân bằng công việc-cuộc sống, phòng ban và chức danh.
- **Đầu ra:** xác suất dự đoán và nhóm rủi ro hiển thị trên giao diện. Ngưỡng nhóm rủi ro hiện là ngưỡng vận hành, chưa được xác nhận phù hợp cho một tổ chức cụ thể.
- **Giới hạn:** dữ liệu không ghi rõ thời điểm đo các đặc trưng, vì vậy chưa xác nhận được đây là dự báo trước sự kiện nghỉ việc. Kết quả hiện tại không bảo đảm khái quát sang doanh nghiệp khác.

---

## 🌟 Điểm nổi bật trong phiên bản v2.0 Hoàn chỉnh

### 1. Giao diện Người dùng (UI/UX) Chuẩn Enterprise SaaS
- **Hệ thống Design System chuyên nghiệp:** Phông chữ Plus Jakarta Sans, bảng màu Slate Dark Navy phối sắc độ Indigo, Emerald, Amber, Rose tinh tế.
- **Thanh điều hướng Sidebar đa nhiệm:** Trạng thái hoạt động của AI Engine (Ready/Heuristic), huy hiệu đếm số lượng nhân sự, thông tin định danh quản trị viên.
- **Tương thích đa thiết bị (Responsive):** Tự động thích ứng trên Desktop màn hình rộng, Tablet và Mobile với menu trượt tiện lợi.
- **Hệ thống Thông báo Toast:** Thông báo tức thì khi thao tác thêm, sửa, xóa, xuất báo cáo thành công.

### 2. Bảng điều khiển Tổng quan & Biểu đồ Tương tác (Dashboard & Charts)
- **4 Thẻ chỉ số KPI cốt lõi:**
  - Tổng số lượng nhân sự (+ xu hướng tăng trưởng).
  - Tổng lượt phân tích AI.
  - Số lượng nhân sự thuộc diện nguy cơ cao (Cần can thiệp giữ chân khẩn cấp).
  - Điểm hài lòng công việc trung bình (thang điểm 1–4).
- **Biểu đồ động (Chart.js):**
  - Biểu đồ cột: Phân bổ nhân sự & Tỷ lệ làm thêm giờ (OT) theo từng phòng ban.
  - Biểu đồ Donut: Cơ cấu phân loại rủi ro (Thấp <35%, Trung bình 35–65%, Cao >65%).
- **Bảng Cảnh báo sớm (Early Attention Warning):** Hiển thị các hồ sơ có OT và chỉ số hài lòng/cân bằng công việc thấp theo dữ liệu hiện có; hỗ trợ nút kích hoạt **⚡ Dự đoán AI tức thì**. Đây là tín hiệu sàng lọc, không phải chẩn đoán kiệt sức.

### 3. Quản lý Hồ sơ Nhân viên Toàn diện (Employee Directory)
- **Tra cứu thời gian thực:** Tìm kiếm theo Mã nhân viên, Họ tên, Phòng ban, Chức danh.
- **Bộ lọc đa tầng:** Lọc theo phòng ban (Sales, R&D, HR) và trạng thái làm thêm giờ (Có OT / Không OT).
- **Thao tác nhanh trên từng hồ sơ:**
  - **⚡ Dự đoán:** Tự động nạp toàn bộ dữ liệu nhân viên sang tab AI để dự báo.
  - **✏️ Chỉnh sửa:** Modal cập nhật thông tin qua API `PUT`.
  - **🗑️ Xóa:** Xóa an toàn kèm hộp thoại xác nhận.
- **Xuất dữ liệu:** Xuất danh sách nhân viên ra tệp **CSV (Excel)** chỉ với 1 click.

### 4. Công cụ Dự đoán Nguy cơ Nghỉ việc AI (AI Attrition Engine)
- **Mô hình Machine Learning:** Pipeline scikit-learn được huấn luyện từ file CSV HR Attrition do giảng viên cung cấp. Script so sánh K-NN, Gaussian Naive Bayes và Decision Tree trên hai cấu hình tiền xử lý, dùng cross-validation để chọn cấu hình và báo cáo kết quả trên tập test độc lập.
- **Kết quả tham khảo:** cấu hình được chọn là Decision Tree, có Accuracy 72,8%, Precision 28,0%, Recall 44,7% và F1 34,4% trên tập test. Xem báo cáo trong `machine_learning/reports/`; các chỉ số này không phải cam kết hiệu năng.
- **Mô phỏng tức thì (Presets):**
  - 🔴 *Nguy cơ rất cao:* Làm OT nhiều, thu nhập thấp, hài lòng 1/4.
  - 🟢 *Gắn bó vững chắc:* Lương cao, thâm niên 8 năm, không OT, hài lòng 4/4.
  - 🟡 *Trung bình:* Cần theo dõi thêm.
- **Đồng hồ đo phần trăm rủi ro (Risk Gauge Meter):** Trực quan hóa xác suất rời đi.
- **Trích xuất nguyên nhân chính (Key Risk Drivers):** Phân tích rõ yếu tố gây rủi ro (Áp lực tăng ca, Mức lương so với thâm niên, Mất cân bằng WLB).
- **Chiến lược giữ chân (Retention Recommendations):** Đề xuất giải pháp nhân sự cụ thể cho HR (Tổ chức Stay Interview 1-1, rà soát chính sách làm thêm, lộ trình thăng tiến).
- Các yếu tố và khuyến nghị hiện được tạo bằng luật nghiệp vụ từ thông tin đầu vào; chúng không phải giải thích nhân quả hoặc phân tích mức đóng góp đặc trưng của mô hình đã huấn luyện.

### 5. Lịch sử Kiểm toán & Báo cáo (Audit Log)
- Lưu trữ toàn bộ các lượt dự đoán kèm thời gian, xác suất, phân loại rủi ro và tên mô hình AI.
- Hỗ trợ xuất nhật ký dự đoán ra tệp **CSV** và xóa lịch sử khi cần.

### 6. Khả năng Chạy Tức thì (Zero Configuration)
- **Mặc định SQLite:** Tự động khởi tạo `hr_attrition.db` và nạp 1.470 hồ sơ từ CSV HR Attrition khi danh sách nhân viên còn trống. CSV không có tên thật, vì vậy ứng dụng tạo tên hiển thị `Employee ####` từ `EmployeeNumber`; lịch sử dự đoán hiện có được giữ lại khi thay hồ sơ.
- **Sẵn sàng cho MySQL (XAMPP):** Nếu muốn dùng MySQL, chỉ cần đổi `DATABASE_URL` trong file `.env`. Nếu MySQL chưa bật, hệ thống tự động fallback về SQLite an toàn mà không bị crash.

---

## Nguồn dữ liệu

Bộ dữ liệu `WA_Fn-UseC_-HR-Employee-Attrition.csv` được cung cấp trong bối cảnh bài tập. Nguồn gốc chính thức và điều khoản phân phối chưa được xác nhận trong repository; hãy xác minh với giảng viên, bổ sung trích dẫn/giấy phép phù hợp và không phân phối lại dữ liệu nếu chưa được cho phép. Chi tiết xử lý dữ liệu và đặc trưng nằm trong [machine_learning/README.md](machine_learning/README.md).

## 🚀 Hướng dẫn Khởi chạy Ứng dụng

### Bước 1: Mở Terminal tại thư mục dự án
```powershell
cd "C:\Users\ADMIN\Downloads\HR_Attrition_Web_v2"
```

### Bước 2: Cài đặt thư viện phụ thuộc (nếu chạy lần đầu)
```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### Bước 3: EDA, đánh giá và huấn luyện mô hình
File dữ liệu nằm tại `machine_learning/data/WA_Fn-UseC_-HR-Employee-Attrition.csv`. Chạy lệnh sau để tạo báo cáo, biểu đồ và huấn luyện lại mô hình:
```powershell
.\.venv\Scripts\python.exe machine_learning\train_model.py
```
Kết quả đánh giá và phân tích lỗi được tạo trong `machine_learning/reports/`.

Để chủ động thay danh sách nhân viên hiện có bằng toàn bộ CSV (1.470 dòng), chạy:
```powershell
.\.venv\Scripts\python.exe -m backend.services.employee_importer --replace
```
Ứng dụng lưu các trường hồ sơ mà web hỗ trợ; nhãn `Attrition` và các cột CSV khác không được đưa vào đầu vào dự đoán.

### Bước 4: Khởi chạy máy chủ Web
```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8000
```

### Bước 5: Trải nghiệm trên trình duyệt
- Giao diện web: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- Tài liệu API tương tác (Swagger UI): [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 📁 Cấu trúc Thư mục Dự án

```
HR_Attrition_Web/
├── backend/
│   ├── routers/
│   │   ├── dashboard.py       # API thống kê tổng quan, tỷ lệ rủi ro, cảnh báo sớm
│   │   ├── employees.py       # API CRUD nhân viên, bộ lọc, seed dữ liệu
│   │   └── predictions.py     # API phân tích AI, lưu và truy vấn lịch sử
│   ├── services/
│   │   └── predictor.py       # Logic AI Engine, phân tích Key Drivers, gợi ý HR
│   ├── database.py            # Kết nối CSDL thông minh (SQLite & MySQL)
│   ├── models.py              # SQLAlchemy Data Models
│   ├── schemas.py             # Pydantic Schemas xác thực dữ liệu
│   └── main.py                # Điểm khởi tạo FastAPI, mount static & router
├── database/
│   └── schema.sql             # Cấu trúc bảng MySQL dự phòng
├── frontend/
│   ├── css/
│   │   └── style.css          # Design System SaaS, responsive, modern cards
│   ├── js/
│   │   └── app.js             # Logic SPA, Chart.js, Toast, Modals, CSV Export
│   └── index.html             # Giao diện chính hoàn chỉnh v2.0
├── machine_learning/
│   ├── data/                  # CSV HR Attrition do giảng viên cung cấp
│   ├── reports/               # Báo cáo EDA, đánh giá, biểu đồ và mẫu dự đoán sai
│   ├── attrition_model.joblib # Pipeline đã huấn luyện trên dữ liệu thật
│   ├── train_model.py         # EDA, cross-validation, đánh giá và huấn luyện
│   └── README.md              # Quy trình và giải thích đặc trưng
├── .env.example               # Mẫu cấu hình; .env cục bộ không đưa lên repository
├── .gitignore                 # Loại trừ môi trường ảo, cache và cấu hình cục bộ
├── requirements.txt           # Danh mục thư viện Python
└── README.md                  # Hướng dẫn chi tiết dự án
```

---

## 🔒 Khuyến cáo Bảo mật & Đạo đức AI
1. Hệ thống phục vụ công tác phân tích, cảnh báo sớm và hỗ trợ đưa ra quyết định quản trị nhân sự.
2. Quyết định tuyển dụng, đãi ngộ hoặc điều chuyển luôn cần sự kết hợp đánh giá thực tế của phòng Nhân sự và Quản lý trực tiếp, không sử dụng AI làm thước đo duy nhất.
3. Bộ dữ liệu mất cân bằng; cần xem Precision, Recall, F1 và các trường hợp dự đoán sai, không chỉ Accuracy.
4. Trước khi dùng trong thực tế, cần kiểm tra quyền sử dụng dữ liệu, xác nhận đặc trưng có trước thời điểm nghỉ việc và đánh giá mô hình trên dữ liệu phù hợp với tổ chức triển khai.
