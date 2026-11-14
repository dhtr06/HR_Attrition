# HR Attrition: thực nghiệm pipeline và mô hình

## Dữ liệu và EDA

- Số mẫu/cột: 1470 / 35.
- Nhãn: nghỉ việc Yes = 237 (16.1%); No = 1233 (83.9%).
- Tổng giá trị thiếu: 0; dòng trùng: 0.
- Dữ liệu mất cân bằng; so sánh Precision/Recall/F1 cùng Accuracy.
- Mã định danh và trường hằng được loại khỏi đặc trưng. Chưa có thời điểm ghi nhận đặc trưng trong file, cần xác nhận chúng xảy ra trước quyết định nghỉ việc.
- Các cột số có ý nghĩa phân loại/thứ bậc được thống kê tần suất và vẽ riêng; các điểm IQR là dấu hiệu cần kiểm tra, không mặc định là lỗi để xóa.
- Pipeline B cấu hình gộp nhóm có dưới 10 mẫu trong train; dữ liệu train hiện tại không có category nào dưới ngưỡng nên khác biệt của B chủ yếu đến từ scaler.

### Mối liên hệ quan sát được

- Tỷ lệ nghỉ việc khác biệt 37.3% giữa `JobRole=Research Director` (2.5%) và `JobRole=Sales Representative` (39.8%). Đây là liên hệ mô tả, không chứng minh quan hệ nhân quả.
- Tỷ lệ nghỉ việc khác biệt 20.1% giữa `OverTime=No` (10.4%) và `OverTime=Yes` (30.5%). Đây là liên hệ mô tả, không chứng minh quan hệ nhân quả.
- Tỷ lệ nghỉ việc khác biệt 17.0% giữa `WorkLifeBalance=3` (14.2%) và `WorkLifeBalance=1` (31.2%). Đây là liên hệ mô tả, không chứng minh quan hệ nhân quả.
- Tương quan Pearson giữa `TotalWorkingYears` và nhãn Attrition (mã hóa Yes=1) là -0.171; không diễn giải tương quan này là quan hệ nhân quả.
- Tương quan Pearson giữa `JobLevel` và nhãn Attrition (mã hóa Yes=1) là -0.169; không diễn giải tương quan này là quan hệ nhân quả.
- Tương quan Pearson giữa `YearsInCurrentRole` và nhãn Attrition (mã hóa Yes=1) là -0.161; không diễn giải tương quan này là quan hệ nhân quả.

## So sánh thực nghiệm

| Pipeline / mô hình | Tham số tốt nhất (CV) | CV F1 | Test Accuracy | Test Precision | Test Recall | Test F1 | Test ROC-AUC |
|---|---|---:|---:|---:|---:|---:|---:|
| Pipeline A / KNeighborsClassifier | `{"classifier__n_neighbors": 5, "classifier__weights": "distance"}` | 0.375 | 0.844 | 0.526 | 0.213 | 0.303 | 0.700 |
| Pipeline A / GaussianNB | `{"classifier__var_smoothing": 1e-09}` | 0.397 | 0.646 | 0.268 | 0.702 | 0.388 | 0.716 |
| Pipeline A / DecisionTreeClassifier | `{"classifier__class_weight": "balanced", "classifier__max_depth": 5, "classifier__min_samples_leaf": 5}` | 0.404 | 0.728 | 0.280 | 0.447 | 0.344 | 0.662 |
| Pipeline B / KNeighborsClassifier | `{"classifier__n_neighbors": 5, "classifier__weights": "distance"}` | 0.398 | 0.844 | 0.526 | 0.213 | 0.303 | 0.688 |
| Pipeline B / GaussianNB | `{"classifier__var_smoothing": 1e-09}` | 0.397 | 0.646 | 0.268 | 0.702 | 0.388 | 0.716 |
| Pipeline B / DecisionTreeClassifier | `{"classifier__class_weight": "balanced", "classifier__max_depth": 5, "classifier__min_samples_leaf": 5}` | 0.404 | 0.728 | 0.280 | 0.447 | 0.344 | 0.662 |

## Kết luận và phân tích lỗi

- Chọn **Pipeline A / DecisionTreeClassifier** theo F1 trung bình cross-validation trên train; test set không được dùng để chọn cấu hình.
- Test set: Accuracy 72.8%, Precision 28.0%, Recall 44.7%, F1 34.4%, ROC-AUC 0.662.
- Baseline dự đoán lớp phổ biến nhất có Accuracy 84.0%, nhưng F1 lớp Yes bằng 0.0%; do đó Accuracy đơn lẻ không thể hiện khả năng tìm nhân viên có nguy cơ.
- Mô hình được chọn có 26 false negative (bỏ sót trường hợp nghỉ việc) và 54 false positive trong test. False negative có thể làm HR bỏ lỡ cơ hội hỗ trợ; false positive có thể dẫn tới can thiệp không cần thiết.

### Phân tích từng pipeline

- **Pipeline A:** StandardScaler giúp K-NN so sánh khoảng cách trên thang đo đồng nhất; One-Hot giữ riêng từng nhóm. Hạn chế: nhạy hơn với ngoại lệ và giữ các nhóm hiếm riêng biệt.
- **Pipeline B:** RobustScaler ít nhạy với ngoại lệ; gộp category hiếm có thể giảm đặc trưng thưa. Hạn chế: có thể làm mất tín hiệu của nhóm nhỏ. Kết quả cụ thể trên cùng tập test/CV:
- **KNeighborsClassifier:** Pipeline B so với A thay đổi F1 CV +0.023 và F1 test +0.000. Mức tăng CV chưa chuyển thành cải thiện trên test.
- **GaussianNB:** Pipeline B so với A thay đổi F1 CV +0.000 và F1 test +0.000. Pipeline B không cải thiện F1 trong lần thử này.
- **DecisionTreeClassifier:** Pipeline B so với A thay đổi F1 CV +0.000 và F1 test +0.000. Pipeline B không cải thiện F1 trong lần thử này.

### Trường hợp dự đoán sai cần lưu ý

- **False negative:** actual `Yes`, predicted `No`, xác suất dự đoán nghỉ việc 0.0%; age=35, monthly_income=4581, years_at_company=11, overtime=Yes, job_satisfaction=4, work_life_balance=4, department=Sales, job_role=Sales Executive. Đây là ví dụ để HR rà soát, không phải kết luận về cá nhân.
- **False negative:** actual `Yes`, predicted `No`, xác suất dự đoán nghỉ việc 0.0%; age=21, monthly_income=2693, years_at_company=1, overtime=No, job_satisfaction=4, work_life_balance=2, department=Research & Development, job_role=Research Scientist. Đây là ví dụ để HR rà soát, không phải kết luận về cá nhân.
- **False positive:** actual `No`, predicted `Yes`, xác suất dự đoán nghỉ việc 97.9%; age=31, monthly_income=1129, years_at_company=1, overtime=Yes, job_satisfaction=4, work_life_balance=3, department=Research & Development, job_role=Laboratory Technician. Đây là ví dụ để HR rà soát, không phải kết luận về cá nhân.
- **False positive:** actual `No`, predicted `Yes`, xác suất dự đoán nghỉ việc 96.3%; age=32, monthly_income=9610, years_at_company=4, overtime=No, job_satisfaction=3, work_life_balance=1, department=Sales, job_role=Sales Executive. Đây là ví dụ để HR rà soát, không phải kết luận về cá nhân.
- False negative đáng lưu ý vì mô hình bỏ sót người thực tế nghỉ việc; false positive có thể gây cảnh báo/can thiệp không cần thiết. Ví dụ trong báo cáo được chọn theo mức độ tự tin của dự đoán, không đại diện cho mọi trường hợp.

### Ưu, nhược điểm mô hình

- **K-NN:** cần chuẩn hóa; có thể bỏ sót nhiều ca nghỉ việc khi ưu tiên precision/độ chính xác tổng thể.
- **GaussianNB:** bắt được nhiều ca nghỉ việc hơn trong lần thử này nhưng false positive nhiều, nên precision thấp.
- **Decision Tree:** dễ giải thích hơn nhưng chất lượng phụ thuộc cách chia cây; F1 test và recall vẫn còn hạn chế.
- Mô hình được chọn có Recall lớp Yes 44.7%; cần cân nhắc chi phí bỏ sót và cảnh báo nhầm trước khi dùng trong quy trình HR.
- Đây là kết quả trên một bộ dữ liệu và một lần chia. Không dùng xác suất mô hình làm căn cứ duy nhất cho quyết định nhân sự.

## Artifact hỗ trợ

- `eda_report.json`: metadata, tần suất, thống kê, tương quan, IQR và leakage review.
- `misclassified_test_cases.csv`: từng hồ sơ test bị dự đoán sai.
- `evaluation_confusion_matrix_roc.png`: ma trận nhầm lẫn và ROC của mô hình được chọn.
