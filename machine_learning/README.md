# Quy trình Machine Learning

## Nguồn dữ liệu

`data/WA_Fn-UseC_-HR-Employee-Attrition.csv` là file CSV do giảng viên cung cấp. Script sử dụng nhãn `Attrition` (`Yes` = 1, `No` = 0). Hãy xác nhận yêu cầu ghi nguồn và giấy phép với giảng viên trước khi phân phối dữ liệu ra ngoài lớp học.

Dữ liệu có 1.470 dòng và 35 cột. 8 đặc trưng được dùng để huấn luyện cũng là các trường mà ứng dụng hiện thu thập:

| Cột CSV | Trường mô hình / ứng dụng |
|---|---|
| `Age` | `age` |
| `MonthlyIncome` | `monthly_income` |
| `YearsAtCompany` | `years_at_company` |
| `OverTime` | `overtime` |
| `JobSatisfaction` | `job_satisfaction` |
| `WorkLifeBalance` | `work_life_balance` |
| `Department` | `department` |
| `JobRole` | `job_role` |

`EmployeeNumber` là mã định danh, còn `EmployeeCount`, `Over18` và `StandardHours` là các trường hằng trong bộ dữ liệu; các trường này không được đưa vào mô hình. Script không tự ý xóa dòng thiếu hoặc trùng: nếu phát hiện vấn đề ở cột cần thiết hoặc có dòng trùng, script dừng và yêu cầu kiểm tra. Báo cáo EDA mô tả tất cả các cột; ý nghĩa cột được ghi theo tên trường và cần đối chiếu với data dictionary chính thức nếu giảng viên cung cấp.

## Chạy EDA, đánh giá và huấn luyện

Từ thư mục gốc dự án:

```powershell
.\.venv\Scripts\python.exe machine_learning\train_model.py
```

Hoặc dùng bộ dữ liệu ở đường dẫn khác:

```powershell
.\.venv\Scripts\python.exe machine_learning\train_model.py --data "C:\duong-dan\HR-Employee-Attrition.csv"
```

Để thay danh sách hồ sơ trên web bằng tất cả dòng của CSV:

```powershell
.\.venv\Scripts\python.exe -m backend.services.employee_importer --replace
```

Lệnh này thay hồ sơ nhân viên đang có, giữ lại lịch sử dự đoán nhưng tách liên kết của lịch sử khỏi hồ sơ mẫu cũ. CSV không có tên nhân viên nên web dùng `Employee ####` làm tên hiển thị và `CSV-####` làm mã nhân viên theo `EmployeeNumber`. Web nhập 1.470 dòng nhưng chỉ lưu các trường hồ sơ mà ứng dụng hỗ trợ; nhãn `Attrition` không được lưu làm đầu vào hoặc hiển thị như kết quả dự đoán.

Script thực hiện:

1. Tạo báo cáo EDA về ý nghĩa/kiểu/cardinality của từng cột, giá trị thiếu/trùng, phân phối nhãn, thống kê và IQR outlier số, tần suất của cả cột phân loại dạng chuỗi lẫn các cột số có ý nghĩa thứ bậc, tương quan số và rà soát cột định danh/hằng/nguy cơ rò rỉ. Sinh histogram, box plot, biểu đồ tần suất phân loại, biểu đồ tần suất biến thứ bậc và heatmap tương quan.
2. Chia train/test theo tỷ lệ 80/20 có stratify và `random_state=42`.
3. So sánh hai pipeline trên cùng dữ liệu: A dùng median/most-frequent imputation, `StandardScaler` và `OneHotEncoder`; B dùng cùng cách điền thiếu, `RobustScaler` và gộp nhóm category hiếm bằng `min_frequency=10`. Với dữ liệu hiện tại không có thiếu, bước imputation là biện pháp phòng vệ, không thay đổi mẫu.
4. Trong mỗi pipeline, dò siêu tham số bằng 5-fold `StratifiedKFold` cho K-NN, Gaussian Naive Bayes và Decision Tree. Chọn cấu hình theo F1 của lớp nghỉ việc (`Yes`) trên các fold train.
5. Đánh giá các cấu hình trên cùng test set bằng Accuracy, Precision, Recall, F1, ROC-AUC và confusion matrix; đồng thời đối chiếu baseline luôn dự đoán lớp phổ biến nhất.
6. Ghi các mẫu test dự đoán sai; báo cáo thêm một số false negative/false positive tiêu biểu, đặc trưng đầu vào và xác suất dự đoán để hỗ trợ phân tích lỗi.
7. Lưu pipeline cuối cùng để ứng dụng FastAPI sử dụng.

Các artifact sinh ra trong `reports/`:

- `eda_report.json`, `eda_overview.png`, `eda_numeric_histograms.png`, `eda_numeric_boxplots.png`, `eda_categorical_frequencies.png`, `eda_ordinal_categorical_frequencies.png` và `eda_numeric_correlations.png`
- `evaluation_report.json` và `evaluation_confusion_matrix_roc.png`
- `misclassified_test_cases.csv`
- `experiment_summary.md`: bảng kết quả, phân tích chênh lệch Pipeline A/B, liên hệ giữa đặc trưng và nhãn, ưu/nhược mô hình, cùng các ví dụ dự đoán sai để tham khảo khi viết báo cáo bài tập.

`evaluation_report.json` có bảng so sánh chéo giữa pipeline A/B và ba thuật toán, siêu tham số tốt nhất, chỉ số cross-validation và test. Khi đọc kết quả, chú ý tỷ lệ nghỉ việc trong dữ liệu chỉ khoảng 16%; Accuracy có thể cao dù mô hình bỏ sót lớp nghỉ việc. Báo cáo rà soát leakage xác định các trường định danh/hằng có thể loại bỏ; bộ dữ liệu không cung cấp thời điểm đo đặc trưng, vì vậy chưa thể kết luận dự đoán là prospective. Cần xác nhận đặc trưng được ghi nhận trước khi nhân viên nghỉ việc. Các liên hệ và ví dụ lỗi trong báo cáo chỉ mang tính mô tả, không chứng minh quan hệ nhân quả và không nên dùng riêng lẻ để ra quyết định nhân sự.

Pipeline B chỉ gộp category nếu tần suất trong tập huấn luyện thấp hơn ngưỡng 10; báo cáo ghi rõ các category thực sự bị gộp. Nếu không có category nào dưới ngưỡng, thay đổi thực tế giữa A và B chủ yếu là scaler, nên không diễn giải lợi ích của gộp nhóm khi dữ liệu không kích hoạt bước đó.

Mô hình đã huấn luyện được lưu tại `attrition_model.joblib`. Pipeline nhận các cột dạng chữ thường như bảng mapping, có `predict_proba`, và nhãn dương `1` là nghỉ việc.

Kết quả trên test set chỉ phản ánh bộ dữ liệu và lần chia này. Bộ dữ liệu mất cân bằng nhãn (nhóm nghỉ việc ít hơn), nên không nên diễn giải Accuracy một mình hay dùng xác suất làm căn cứ duy nhất cho quyết định nhân sự. Ứng dụng hiện chỉ thu thập 8 đặc trưng, vì vậy không sử dụng toàn bộ 35 cột trong bộ dữ liệu.
