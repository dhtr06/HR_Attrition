import argparse
import json
from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import (
    GridSearchCV,
    StratifiedKFold,
    train_test_split,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, RobustScaler, StandardScaler
from sklearn.tree import DecisionTreeClassifier


ROOT_DIR = Path(__file__).resolve().parent
DEFAULT_DATASET = ROOT_DIR / "data" / "WA_Fn-UseC_-HR-Employee-Attrition.csv"
MODEL_PATH = ROOT_DIR / "attrition_model.joblib"
REPORT_DIR = ROOT_DIR / "reports"

SOURCE_TO_FEATURE = {
    "Age": "age",
    "MonthlyIncome": "monthly_income",
    "YearsAtCompany": "years_at_company",
    "OverTime": "overtime",
    "JobSatisfaction": "job_satisfaction",
    "WorkLifeBalance": "work_life_balance",
    "Department": "department",
    "JobRole": "job_role",
}
FEATURE_COLUMNS = list(SOURCE_TO_FEATURE.values())
INFREQUENT_CATEGORY_MIN_FREQUENCY = 10
ORDINAL_CATEGORICAL_COLUMNS = [
    "Education",
    "EnvironmentSatisfaction",
    "JobInvolvement",
    "JobLevel",
    "JobSatisfaction",
    "PerformanceRating",
    "RelationshipSatisfaction",
    "StockOptionLevel",
    "WorkLifeBalance",
]
NUMERIC_FEATURES = [
    "age",
    "monthly_income",
    "years_at_company",
    "job_satisfaction",
    "work_life_balance",
]
CATEGORICAL_FEATURES = ["overtime", "department", "job_role"]
SCORING = {
    "accuracy": "accuracy",
    "precision": "precision",
    "recall": "recall",
    "f1": "f1",
    "roc_auc": "roc_auc",
}
RANDOM_STATE = 42


def _write_json(path: Path, data: dict) -> None:
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False),
        encoding="utf-8",
    )


def _write_experiment_summary(
    path: Path,
    eda_report: dict,
    evaluation_report: dict,
) -> None:
    comparison = evaluation_report["cross_validation"]["comparison"]
    infrequent_categories = evaluation_report[
        "pipeline_b_infrequent_categories_training"
    ]
    numeric_target_correlations = {
        feature: values["Attrition"]
        for feature, values in eda_report[
            "numeric_correlation_matrix_including_target"
        ].items()
        if feature != "Attrition"
    }
    strongest_correlations = sorted(
        numeric_target_correlations.items(),
        key=lambda item: abs(item[1]),
        reverse=True,
    )[:3]
    feature_rate_spreads = []
    for feature, groups in eda_report["attrition_rates_by_feature"].items():
        if len(groups) < 2:
            continue
        lowest = min(groups, key=lambda group: group["attrition_rate"])
        highest = max(groups, key=lambda group: group["attrition_rate"])
        feature_rate_spreads.append(
            (highest["attrition_rate"] - lowest["attrition_rate"], feature, lowest, highest)
        )
    feature_rate_spreads.sort(reverse=True, key=lambda item: item[0])

    pipeline_comparisons = []
    for algorithm in dict.fromkeys(result["algorithm"] for result in comparison.values()):
        pipeline_a = comparison[f"Pipeline A / {algorithm}"]
        pipeline_b = comparison[f"Pipeline B / {algorithm}"]
        cv_delta = (
            pipeline_b["cross_validation_mean"]["f1"]
            - pipeline_a["cross_validation_mean"]["f1"]
        )
        test_delta = pipeline_b["test_metrics"]["f1"] - pipeline_a["test_metrics"]["f1"]
        pipeline_comparisons.append(
            f"- **{algorithm}:** Pipeline B so với A thay đổi F1 CV "
            f"{cv_delta:+.3f} và F1 test {test_delta:+.3f}. "
            + (
                "Mức tăng CV chưa chuyển thành cải thiện trên test."
                if cv_delta > 0 and test_delta <= 0
                else "Kết quả test cải thiện, nhưng cần xác nhận trên lần chia hoặc dữ liệu khác."
                if test_delta > 0
                else "Pipeline B không cải thiện F1 trong lần thử này."
            )
        )

    error_examples = evaluation_report["error_analysis"]["examples"]
    formatted_error_examples = []
    for example in error_examples:
        feature_text = ", ".join(
            f"{feature}={value}" for feature, value in example["features"].items()
        )
        formatted_error_examples.append(
            f"- **{example['error_type']}:** actual `{example['actual']}`, "
            f"predicted `{example['predicted']}`, xác suất dự đoán nghỉ việc "
            f"{example['predicted_attrition_probability']:.1%}; {feature_text}. "
            f"Đây là ví dụ để HR rà soát, không phải kết luận về cá nhân."
        )

    lines = [
        "# HR Attrition: thực nghiệm pipeline và mô hình",
        "",
        "## Dữ liệu và EDA",
        "",
        f"- Số mẫu/cột: {eda_report['rows']} / {eda_report['columns']}.",
        f"- Nhãn: nghỉ việc Yes = {eda_report['attrition_counts']['Yes']} "
        f"({eda_report['attrition_rates']['Yes']:.1%}); "
        f"No = {eda_report['attrition_counts']['No']} "
        f"({eda_report['attrition_rates']['No']:.1%}).",
        f"- Tổng giá trị thiếu: {sum(eda_report['missing_values_by_column'].values())}; "
        f"dòng trùng: {eda_report['duplicate_rows']}.",
        "- Dữ liệu mất cân bằng; so sánh Precision/Recall/F1 cùng Accuracy.",
        "- Mã định danh và trường hằng được loại khỏi đặc trưng. Chưa có thời điểm ghi nhận "
        "đặc trưng trong file, cần xác nhận chúng xảy ra trước quyết định nghỉ việc.",
        "- Các cột số có ý nghĩa phân loại/thứ bậc được thống kê tần suất và vẽ riêng; "
        "các điểm IQR là dấu hiệu cần kiểm tra, không mặc định là lỗi để xóa.",
        (
            "- Pipeline B cấu hình gộp nhóm có dưới "
            f"{INFREQUENT_CATEGORY_MIN_FREQUENCY} mẫu trong train; dữ liệu train hiện tại "
            "không có category nào dưới ngưỡng nên khác biệt của B chủ yếu đến từ scaler."
            if not any(infrequent_categories.values())
            else "- Các category Pipeline B gộp (chỉ xác định trên train): "
            + "; ".join(
                f"{feature}: {', '.join(values)}"
                for feature, values in infrequent_categories.items()
                if values
            )
            + "."
        ),
        "",
        "### Mối liên hệ quan sát được",
        "",
        *[
            f"- Tỷ lệ nghỉ việc khác biệt {spread:.1%} giữa "
            f"`{feature}={lowest['value']}` ({lowest['attrition_rate']:.1%}) và "
            f"`{feature}={highest['value']}` ({highest['attrition_rate']:.1%}). "
            "Đây là liên hệ mô tả, không chứng minh quan hệ nhân quả."
            for spread, feature, lowest, highest in feature_rate_spreads[:3]
        ],
        *[
            f"- Tương quan Pearson giữa `{feature}` và nhãn Attrition (mã hóa Yes=1) "
            f"là {correlation:+.3f}; không diễn giải tương quan này là quan hệ nhân quả."
            for feature, correlation in strongest_correlations
        ],
        "",
        "## So sánh thực nghiệm",
        "",
        "| Pipeline / mô hình | Tham số tốt nhất (CV) | CV F1 | Test Accuracy | Test Precision | Test Recall | Test F1 | Test ROC-AUC |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for name, result in comparison.items():
        cv = result["cross_validation_mean"]
        test = result["test_metrics"]
        parameters = json.dumps(result["best_parameters"], ensure_ascii=False, sort_keys=True)
        lines.append(
            f"| {name} | `{parameters}` | {cv['f1']:.3f} | {test['accuracy']:.3f} | "
            f"{test['precision']:.3f} | {test['recall']:.3f} | {test['f1']:.3f} | "
            f"{test['roc_auc']:.3f} |"
        )

    lines.extend(
        [
            "",
            "## Kết luận và phân tích lỗi",
            "",
            f"- Chọn **{evaluation_report['selected_comparison']}** theo F1 trung bình "
            "cross-validation trên train; test set không được dùng để chọn cấu hình.",
            f"- Test set: Accuracy {evaluation_report['test_metrics']['accuracy']:.1%}, "
            f"Precision {evaluation_report['test_metrics']['precision']:.1%}, "
            f"Recall {evaluation_report['test_metrics']['recall']:.1%}, "
            f"F1 {evaluation_report['test_metrics']['f1']:.1%}, "
            f"ROC-AUC {evaluation_report['test_metrics']['roc_auc']:.3f}.",
            f"- Baseline dự đoán lớp phổ biến nhất có Accuracy "
            f"{evaluation_report['majority_class_baseline_test_metrics']['accuracy']:.1%}, "
            f"nhưng F1 lớp Yes bằng "
            f"{evaluation_report['majority_class_baseline_test_metrics']['f1']:.1%}; "
            "do đó Accuracy đơn lẻ không thể hiện khả năng tìm nhân viên có nguy cơ.",
            f"- Mô hình được chọn có {evaluation_report['error_analysis']['false_negatives_attrition_missed']} "
            "false negative (bỏ sót trường hợp nghỉ việc) và "
            f"{evaluation_report['error_analysis']['false_positives_false_alerts']} "
            "false positive trong test. False negative có thể làm HR bỏ lỡ cơ hội hỗ trợ; "
            "false positive có thể dẫn tới can thiệp không cần thiết.",
            "",
            "### Phân tích từng pipeline",
            "",
            "- **Pipeline A:** StandardScaler giúp K-NN so sánh khoảng cách trên thang đo "
            "đồng nhất; One-Hot giữ riêng từng nhóm. Hạn chế: nhạy hơn với ngoại lệ và giữ "
            "các nhóm hiếm riêng biệt.",
            "- **Pipeline B:** RobustScaler ít nhạy với ngoại lệ; gộp category hiếm có thể "
            "giảm đặc trưng thưa. Hạn chế: có thể làm mất tín hiệu của nhóm nhỏ. Kết quả "
            "cụ thể trên cùng tập test/CV:",
            *pipeline_comparisons,
            "",
            "### Trường hợp dự đoán sai cần lưu ý",
            "",
            *formatted_error_examples,
            "- False negative đáng lưu ý vì mô hình bỏ sót người thực tế nghỉ việc; false "
            "positive có thể gây cảnh báo/can thiệp không cần thiết. Ví dụ trong báo cáo "
            "được chọn theo mức độ tự tin của dự đoán, không đại diện cho mọi trường hợp.",
            "",
            "### Ưu, nhược điểm mô hình",
            "",
            "- **K-NN:** cần chuẩn hóa; có thể bỏ sót nhiều ca nghỉ việc khi ưu tiên "
            "precision/độ chính xác tổng thể.",
            "- **GaussianNB:** bắt được nhiều ca nghỉ việc hơn trong lần thử này nhưng "
            "false positive nhiều, nên precision thấp.",
            "- **Decision Tree:** dễ giải thích hơn nhưng chất lượng phụ thuộc cách chia "
            "cây; F1 test và recall vẫn còn hạn chế.",
            "- Mô hình được chọn có Recall lớp Yes "
            f"{evaluation_report['test_metrics']['recall']:.1%}; cần cân nhắc chi phí bỏ "
            "sót và cảnh báo nhầm trước khi dùng trong quy trình HR.",
            "- Đây là kết quả trên một bộ dữ liệu và một lần chia. Không dùng xác suất mô hình "
            "làm căn cứ duy nhất cho quyết định nhân sự.",
            "",
            "## Artifact hỗ trợ",
            "",
            "- `eda_report.json`: metadata, tần suất, thống kê, tương quan, IQR và leakage review.",
            "- `misclassified_test_cases.csv`: từng hồ sơ test bị dự đoán sai.",
            "- `evaluation_confusion_matrix_roc.png`: ma trận nhầm lẫn và ROC của mô hình được chọn.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def _make_preprocessor(configuration: str) -> ColumnTransformer:
    if configuration == "A":
        numeric_scaler = StandardScaler()
        categorical_encoder = OneHotEncoder(
            handle_unknown="ignore",
            sparse_output=False,
        )
    elif configuration == "B":
        numeric_scaler = RobustScaler()
        categorical_encoder = OneHotEncoder(
            handle_unknown="ignore",
            min_frequency=INFREQUENT_CATEGORY_MIN_FREQUENCY,
            sparse_output=False,
        )
    else:
        raise ValueError(f"Unknown preprocessing configuration: {configuration}")

    return ColumnTransformer(
        transformers=[
            (
                "numeric",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scaler", numeric_scaler),
                    ]
                ),
                NUMERIC_FEATURES,
            ),
            (
                "categorical",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("encoder", categorical_encoder),
                    ]
                ),
                CATEGORICAL_FEATURES,
            ),
        ]
    )


def _build_model_searches(configuration: str, cross_validation) -> dict:
    preprocessing = _make_preprocessor(configuration)
    model_grids = {
        "KNeighborsClassifier": (
            KNeighborsClassifier(),
            {
                "classifier__n_neighbors": [5, 11, 21],
                "classifier__weights": ["uniform", "distance"],
            },
        ),
        "GaussianNB": (
            GaussianNB(),
            {"classifier__var_smoothing": [1e-9, 1e-8, 1e-7]},
        ),
        "DecisionTreeClassifier": (
            DecisionTreeClassifier(random_state=RANDOM_STATE),
            {
                "classifier__max_depth": [None, 5, 10],
                "classifier__min_samples_leaf": [1, 5],
                "classifier__class_weight": [None, "balanced"],
            },
        ),
    }

    return {
        model_name: GridSearchCV(
            estimator=Pipeline(
                steps=[
                    ("preprocessor", preprocessing),
                    ("classifier", estimator),
                ]
            ),
            param_grid=parameter_grid,
            scoring=SCORING,
            refit="f1",
            cv=cross_validation,
            n_jobs=-1,
            return_train_score=False,
        )
        for model_name, (estimator, parameter_grid) in model_grids.items()
    }


def _build_eda_report(data: pd.DataFrame) -> dict:
    target_counts = data["Attrition"].value_counts().reindex(["No", "Yes"], fill_value=0)
    excluded_from_feature_analysis = {
        "EmployeeNumber",
        "EmployeeCount",
        "Over18",
        "StandardHours",
    }
    numeric_columns = [
        column
        for column in data.select_dtypes(include="number").columns
        if column not in excluded_from_feature_analysis
    ]
    categorical_columns = [
        column
        for column in data.select_dtypes(exclude="number").columns
        if column != "Attrition"
    ]
    numeric_summary = data[numeric_columns].describe().round(3).to_dict()
    categorical_frequencies = {}
    categorical_rates = {}
    for column in categorical_columns:
        frequencies = data[column].value_counts(dropna=False)
        categorical_frequencies[column] = {
            str(value): int(count) for value, count in frequencies.items()
        }

    for column in [
        "OverTime",
        "Department",
        "JobRole",
        "JobSatisfaction",
        "WorkLifeBalance",
    ]:
        grouped = data.groupby(column, dropna=False)["Attrition"].agg(
            count="size",
            attrition_count=lambda values: (values == "Yes").sum(),
            attrition_rate=lambda values: (values == "Yes").mean(),
        )
        categorical_rates[column] = [
            {
                "value": str(value),
                "count": int(row["count"]),
                "attrition_count": int(row["attrition_count"]),
                "attrition_rate": round(float(row["attrition_rate"]), 4),
            }
            for value, row in grouped.iterrows()
        ]

    numeric_data = data[numeric_columns].copy()
    numeric_data["Attrition"] = data["Attrition"].map({"No": 0, "Yes": 1})
    numeric_correlation = numeric_data.corr(numeric_only=True)
    outlier_summary = {}
    for column in numeric_columns:
        values = data[column].dropna()
        q1, q3 = values.quantile([0.25, 0.75])
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        outlier_summary[column] = {
            "lower_iqr_bound": float(lower_bound),
            "upper_iqr_bound": float(upper_bound),
            "outlier_count": int(((values < lower_bound) | (values > upper_bound)).sum()),
        }

    column_meanings = {
        "Age": "Employee age in years",
        "Attrition": "Target label: whether the employee left",
        "BusinessTravel": "Business travel frequency",
        "DailyRate": "Daily pay/rate value",
        "Department": "Organizational department",
        "DistanceFromHome": "Distance from home to workplace",
        "Education": "Education level",
        "EducationField": "Field of education",
        "EmployeeCount": "Constant employee count field",
        "EmployeeNumber": "Unique employee identifier",
        "EnvironmentSatisfaction": "Satisfaction with work environment",
        "Gender": "Employee gender",
        "HourlyRate": "Hourly pay/rate value",
        "JobInvolvement": "Level of job involvement",
        "JobLevel": "Job seniority level",
        "JobRole": "Employee job role",
        "JobSatisfaction": "Job satisfaction level",
        "MaritalStatus": "Marital status",
        "MonthlyIncome": "Monthly income",
        "MonthlyRate": "Monthly pay/rate value",
        "NumCompaniesWorked": "Number of previous companies worked",
        "Over18": "Constant indicator that employees are over 18",
        "OverTime": "Whether the employee works overtime",
        "PercentSalaryHike": "Percentage salary increase",
        "PerformanceRating": "Performance rating",
        "RelationshipSatisfaction": "Relationship satisfaction level",
        "StandardHours": "Constant standard-hours field",
        "StockOptionLevel": "Stock option level",
        "TotalWorkingYears": "Total years of work experience",
        "TrainingTimesLastYear": "Training sessions in the last year",
        "WorkLifeBalance": "Work-life balance rating",
        "YearsAtCompany": "Years employed at the company",
        "YearsInCurrentRole": "Years in the current role",
        "YearsSinceLastPromotion": "Years since the last promotion",
        "YearsWithCurrManager": "Years with the current manager",
    }

    return {
        "dataset": "WA_Fn-UseC_-HR-Employee-Attrition.csv",
        "rows": int(data.shape[0]),
        "columns": int(data.shape[1]),
        "column_names": data.columns.tolist(),
        "columns_metadata": {
            column: {
                "dtype": str(data[column].dtype),
                "meaning": column_meanings.get(column, "Meaning requires confirmation from the dataset documentation"),
                "unique_values": int(data[column].nunique(dropna=False)),
            }
            for column in data.columns
        },
        "missing_values_by_column": {
            column: int(count) for column, count in data.isna().sum().items()
        },
        "duplicate_rows": int(data.duplicated().sum()),
        "attrition_counts": {label: int(count) for label, count in target_counts.items()},
        "attrition_rates": {
            label: round(float(count / len(data)), 4)
            for label, count in target_counts.items()
        },
        "numeric_summary": numeric_summary,
        "numeric_iqr_outlier_summary": outlier_summary,
        "numeric_correlation_matrix_including_target": numeric_correlation.round(4).to_dict(),
        "categorical_value_frequencies": categorical_frequencies,
        "ordinal_categorical_columns": ORDINAL_CATEGORICAL_COLUMNS,
        "ordinal_categorical_value_frequencies": {
            column: {
                str(value): int(count)
                for value, count in data[column].value_counts(dropna=False).items()
            }
            for column in ORDINAL_CATEGORICAL_COLUMNS
            if column in data.columns
        },
        "attrition_rates_by_feature": categorical_rates,
        "features_used_by_model": FEATURE_COLUMNS,
        "excluded_identifier_and_constant_columns": [
            "EmployeeNumber",
            "EmployeeCount",
            "Over18",
            "StandardHours",
        ],
        "leakage_review": {
            "EmployeeNumber": "Excluded: unique identifier with no predictive business meaning.",
            "EmployeeCount": "Excluded: constant column with no predictive information.",
            "Over18": "Excluded: constant column with no predictive information.",
            "StandardHours": "Excluded: constant column with no predictive information.",
            "Attrition": "Target only; never included in the input features.",
            "other_columns": "The dataset does not establish feature observation timestamps. Confirm with the instructor that each selected feature is measured before the attrition outcome.",
        },
    }


def _save_eda_plots(data: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    counts = data["Attrition"].value_counts().reindex(["No", "Yes"], fill_value=0)
    axes[0].bar(counts.index, counts.values, color=["#4f46e5", "#ef4444"])
    axes[0].set_title("Attrition class distribution")
    axes[0].set_ylabel("Number of employees")
    for index, value in enumerate(counts.values):
        axes[0].text(index, value, str(value), ha="center", va="bottom")

    overtime_rate = data.groupby("OverTime")["Attrition"].apply(
        lambda values: (values == "Yes").mean()
    )
    axes[1].bar(overtime_rate.index, overtime_rate.values, color="#f59e0b")
    axes[1].set_title("Attrition rate by overtime")
    axes[1].set_ylabel("Attrition rate")
    axes[1].set_ylim(0, max(0.1, float(overtime_rate.max()) * 1.2))
    axes[1].yaxis.set_major_formatter(plt.FuncFormatter(lambda value, _: f"{value:.0%}"))

    satisfaction_rate = data.groupby("JobSatisfaction")["Attrition"].apply(
        lambda values: (values == "Yes").mean()
    )
    axes[2].bar(satisfaction_rate.index.astype(str), satisfaction_rate.values, color="#10b981")
    axes[2].set_title("Attrition rate by job satisfaction")
    axes[2].set_xlabel("Job satisfaction (1-4)")
    axes[2].set_ylabel("Attrition rate")
    axes[2].set_ylim(0, max(0.1, float(satisfaction_rate.max()) * 1.2))
    axes[2].yaxis.set_major_formatter(plt.FuncFormatter(lambda value, _: f"{value:.0%}"))
    fig.tight_layout()
    fig.savefig(REPORT_DIR / "eda_overview.png", dpi=160)
    plt.close(fig)

    excluded = {"EmployeeNumber", "EmployeeCount", "Over18", "StandardHours"}
    numeric_columns = [
        column
        for column in data.select_dtypes(include="number").columns
        if column not in excluded and data[column].nunique() > 1
    ]
    columns_per_row = 4
    rows = (len(numeric_columns) + columns_per_row - 1) // columns_per_row
    fig, axes = plt.subplots(rows, columns_per_row, figsize=(16, rows * 3.2))
    for axis, column in zip(axes.flat, numeric_columns):
        axis.hist(data[column], bins=20, color="#4f46e5", alpha=0.8)
        axis.set_title(column)
        axis.set_ylabel("Count")
    for axis in axes.flat[len(numeric_columns):]:
        axis.set_visible(False)
    fig.suptitle("Numeric feature distributions", y=1.002)
    fig.tight_layout()
    fig.savefig(REPORT_DIR / "eda_numeric_histograms.png", dpi=160, bbox_inches="tight")
    plt.close(fig)

    fig, axes = plt.subplots(rows, columns_per_row, figsize=(16, rows * 3.2))
    for axis, column in zip(axes.flat, numeric_columns):
        axis.boxplot(data[column].dropna(), orientation="vertical")
        axis.set_title(column)
        axis.set_ylabel("Value")
    for axis in axes.flat[len(numeric_columns):]:
        axis.set_visible(False)
    fig.suptitle("Numeric feature box plots (IQR outliers are summarized in EDA JSON)", y=1.002)
    fig.tight_layout()
    fig.savefig(REPORT_DIR / "eda_numeric_boxplots.png", dpi=160, bbox_inches="tight")
    plt.close(fig)

    categorical_columns = [
        column
        for column in data.select_dtypes(exclude="number").columns
        if column != "Attrition"
    ]
    columns_per_row = 3
    rows = (len(categorical_columns) + columns_per_row - 1) // columns_per_row
    fig, axes = plt.subplots(rows, columns_per_row, figsize=(18, rows * 3.6))
    for axis, column in zip(axes.flat, categorical_columns):
        frequencies = data[column].value_counts().sort_values(ascending=False)
        axis.bar(range(len(frequencies)), frequencies.values, color="#10b981")
        axis.set_title(column)
        axis.set_xticks(range(len(frequencies)), labels=frequencies.index.astype(str), rotation=60, ha="right")
        axis.set_ylabel("Count")
    for axis in axes.flat[len(categorical_columns):]:
        axis.set_visible(False)
    fig.suptitle("Categorical feature frequencies", y=1.002)
    fig.tight_layout()
    fig.savefig(REPORT_DIR / "eda_categorical_frequencies.png", dpi=160, bbox_inches="tight")
    plt.close(fig)

    ordinal_categorical_columns = [
        column for column in ORDINAL_CATEGORICAL_COLUMNS if column in data.columns
    ]
    columns_per_row = 3
    rows = (len(ordinal_categorical_columns) + columns_per_row - 1) // columns_per_row
    fig, axes = plt.subplots(rows, columns_per_row, figsize=(18, rows * 3.6))
    for axis, column in zip(axes.flat, ordinal_categorical_columns):
        frequencies = data[column].value_counts(dropna=False).sort_index()
        axis.bar(frequencies.index.astype(str), frequencies.values, color="#0ea5e9")
        axis.set_title(column)
        axis.set_xlabel("Ordinal category")
        axis.set_ylabel("Count")
    for axis in axes.flat[len(ordinal_categorical_columns):]:
        axis.set_visible(False)
    fig.suptitle("Ordinal numeric-category frequencies", y=1.002)
    fig.tight_layout()
    fig.savefig(
        REPORT_DIR / "eda_ordinal_categorical_frequencies.png",
        dpi=160,
        bbox_inches="tight",
    )
    plt.close(fig)

    correlation_columns = numeric_columns + ["Attrition"]
    numeric_data = data[numeric_columns].copy()
    numeric_data["Attrition"] = data["Attrition"].map({"No": 0, "Yes": 1})
    correlation = numeric_data.corr(numeric_only=True)
    fig, axis = plt.subplots(figsize=(max(10, len(correlation_columns) * 0.55), 9))
    image = axis.imshow(correlation, cmap="coolwarm", vmin=-1, vmax=1, aspect="auto")
    axis.set_xticks(range(len(correlation_columns)), labels=correlation_columns, rotation=90)
    axis.set_yticks(range(len(correlation_columns)), labels=correlation_columns)
    axis.set_title("Numeric feature and target correlation")
    fig.colorbar(image, ax=axis, fraction=0.025, pad=0.02)
    fig.tight_layout()
    fig.savefig(REPORT_DIR / "eda_numeric_correlations.png", dpi=160, bbox_inches="tight")
    plt.close(fig)


def _metrics(y_true, y_pred, probabilities) -> dict:
    matrix = confusion_matrix(y_true, y_pred, labels=[0, 1])
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_true, probabilities)),
        "confusion_matrix_labels": ["No", "Yes"],
        "confusion_matrix": matrix.tolist(),
        "classification_report": classification_report(
            y_true,
            y_pred,
            labels=[0, 1],
            target_names=["No", "Yes"],
            output_dict=True,
            zero_division=0,
        ),
    }


def _save_evaluation_plot(y_true, y_pred, probabilities, output_path: Path) -> None:
    matrix = confusion_matrix(y_true, y_pred, labels=[0, 1])
    false_positive_rate, true_positive_rate, _ = roc_curve(y_true, probabilities)
    auc = roc_auc_score(y_true, probabilities)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    image = axes[0].imshow(matrix, cmap="Blues")
    axes[0].set_title("Confusion matrix")
    axes[0].set_xlabel("Predicted label")
    axes[0].set_ylabel("Actual label")
    axes[0].set_xticks([0, 1], labels=["No", "Yes"])
    axes[0].set_yticks([0, 1], labels=["No", "Yes"])
    for row in range(2):
        for column in range(2):
            axes[0].text(column, row, str(matrix[row, column]), ha="center", va="center")
    fig.colorbar(image, ax=axes[0], fraction=0.046, pad=0.04)

    axes[1].plot(false_positive_rate, true_positive_rate, label=f"AUC = {auc:.3f}")
    axes[1].plot([0, 1], [0, 1], linestyle="--", color="gray")
    axes[1].set_title("ROC curve")
    axes[1].set_xlabel("False positive rate")
    axes[1].set_ylabel("True positive rate")
    axes[1].legend(loc="lower right")

    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def train_and_evaluate(dataset_path: Path = DEFAULT_DATASET) -> dict:
    if not dataset_path.is_file():
        raise FileNotFoundError(
            f"Dataset not found: {dataset_path}. "
            "Place the instructor CSV in machine_learning/data or pass --data."
        )

    data = pd.read_csv(dataset_path)
    required_columns = set(SOURCE_TO_FEATURE) | {"Attrition"}
    missing_columns = sorted(required_columns - set(data.columns))
    if missing_columns:
        raise ValueError(f"Dataset is missing required columns: {missing_columns}")

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    eda_report = _build_eda_report(data)
    _write_json(REPORT_DIR / "eda_report.json", eda_report)
    _save_eda_plots(data)

    missing_required = data[list(required_columns)].isna().sum()
    missing_required = {column: int(count) for column, count in missing_required.items() if count}
    if missing_required:
        raise ValueError(f"Required columns contain missing values: {missing_required}")

    duplicate_count = int(data.duplicated().sum())
    if duplicate_count:
        raise ValueError(
            f"Dataset contains {duplicate_count} duplicate rows. "
            "Review them before training; the script will not silently remove records."
        )

    unknown_labels = sorted(set(data["Attrition"].astype(str)) - {"No", "Yes"})
    if unknown_labels:
        raise ValueError(f"Unexpected Attrition labels: {unknown_labels}")

    features = data.rename(columns=SOURCE_TO_FEATURE)[FEATURE_COLUMNS].copy()
    target = data["Attrition"].map({"No": 0, "Yes": 1})
    X_train, X_test, y_train, y_test = train_test_split(
        features,
        target,
        test_size=0.2,
        random_state=RANDOM_STATE,
        stratify=target,
    )

    cross_validation = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    infrequent_categories = {
        feature: [
            str(value)
            for value, count in X_train[feature].value_counts().items()
            if count < INFREQUENT_CATEGORY_MIN_FREQUENCY
        ]
        for feature in CATEGORICAL_FEATURES
    }
    comparison_results = {}
    evaluated_searches = {}
    for configuration in ["A", "B"]:
        for model_name, search in _build_model_searches(configuration, cross_validation).items():
            search.fit(X_train, y_train)
            best_index = search.best_index_
            key = f"Pipeline {configuration} / {model_name}"
            cv_metrics = {
                metric: float(search.cv_results_[f"mean_test_{metric}"][best_index])
                for metric in SCORING
            }
            predictions = search.best_estimator_.predict(X_test)
            probabilities = search.best_estimator_.predict_proba(X_test)[:, 1]
            holdout_metrics = _metrics(y_test, predictions, probabilities)
            comparison_results[key] = {
                "preprocessing_pipeline": configuration,
                "algorithm": model_name,
                "best_parameters": search.best_params_,
                "cross_validation_mean": cv_metrics,
                "test_metrics": {
                    metric: holdout_metrics[metric] for metric in SCORING
                },
                "confusion_matrix": holdout_metrics["confusion_matrix"],
            }
            evaluated_searches[key] = search

    selected_key = max(
        comparison_results,
        key=lambda key: comparison_results[key]["cross_validation_mean"]["f1"],
    )
    selected_search = evaluated_searches[selected_key]
    selected_model = selected_search.best_estimator_
    selected_result = comparison_results[selected_key]
    selected_model_name = selected_result["algorithm"]
    selected_pipeline_name = selected_result["preprocessing_pipeline"]
    selected_parameters = selected_result["best_parameters"]
    predictions = selected_model.predict(X_test)
    probabilities = selected_model.predict_proba(X_test)[:, 1]
    test_metrics = _metrics(y_test, predictions, probabilities)
    majority_baseline = DummyClassifier(strategy="most_frequent").fit(X_train, y_train)
    baseline_predictions = majority_baseline.predict(X_test)
    baseline_probabilities = majority_baseline.predict_proba(X_test)[:, 1]
    baseline_metrics = _metrics(y_test, baseline_predictions, baseline_probabilities)

    misclassified = X_test.reset_index(drop=True).copy()
    misclassified["actual_attrition"] = y_test.reset_index(drop=True).map({0: "No", 1: "Yes"})
    misclassified["predicted_attrition"] = pd.Series(predictions).map({0: "No", 1: "Yes"})
    misclassified["predicted_attrition_probability"] = probabilities
    misclassified = misclassified[
        misclassified["actual_attrition"] != misclassified["predicted_attrition"]
    ]
    misclassified.to_csv(REPORT_DIR / "misclassified_test_cases.csv", index=False)
    false_negatives = int(((y_test == 1) & (predictions == 0)).sum())
    false_positives = int(((y_test == 0) & (predictions == 1)).sum())
    misclassified_records = misclassified.to_dict(orient="records")
    false_negative_examples = sorted(
        (
            row
            for row in misclassified_records
            if row["actual_attrition"] == "Yes"
        ),
        key=lambda row: row["predicted_attrition_probability"],
    )[:2]
    false_positive_examples = sorted(
        (
            row
            for row in misclassified_records
            if row["actual_attrition"] == "No"
        ),
        key=lambda row: row["predicted_attrition_probability"],
        reverse=True,
    )[:2]

    def format_error_example(row: dict, error_type: str) -> dict:
        return {
            "error_type": error_type,
            "actual": row["actual_attrition"],
            "predicted": row["predicted_attrition"],
            "predicted_attrition_probability": float(
                row["predicted_attrition_probability"]
            ),
            "features": {
                feature: row[feature]
                for feature in FEATURE_COLUMNS
            },
        }

    _save_evaluation_plot(
        y_test,
        predictions,
        probabilities,
        REPORT_DIR / "evaluation_confusion_matrix_roc.png",
    )
    evaluation_report = {
        "dataset": dataset_path.name,
        "target_definition": {"No": 0, "Yes": 1},
        "random_state": RANDOM_STATE,
        "split": {
            "strategy": "stratified train/test split",
            "test_size": 0.2,
            "training_rows": int(len(X_train)),
            "test_rows": int(len(X_test)),
            "training_attrition_counts": {
                "No": int((y_train == 0).sum()),
                "Yes": int((y_train == 1).sum()),
            },
            "test_attrition_counts": {
                "No": int((y_test == 0).sum()),
                "Yes": int((y_test == 1).sum()),
            },
        },
        "preprocessing_pipelines": {
            "A": {
                "description": "Numeric median imputation + StandardScaler; categorical most-frequent imputation + One-Hot Encoding.",
                "purpose": "Baseline pipeline. Scaling centers numeric variables and OHE retains each category.",
            },
            "B": {
                "description": "Same leakage-safe imputers + RobustScaler; One-Hot Encoding groups categories with fewer than 10 training samples.",
                "purpose": "Improved preprocessing hypothesis: robust scaling reduces outlier influence and infrequent-category grouping reduces sparse/noisy categories. Validate the benefit using the same stratified folds.",
            },
        },
        "pipeline_b_infrequent_categories_training": infrequent_categories,
        "cross_validation": {
            "strategy": "5-fold StratifiedKFold on training data",
            "selection_metric": "f1 for the attrition (Yes) class",
            "comparison": comparison_results,
        },
        "selected_comparison": selected_key,
        "selected_model": selected_model_name,
        "selected_preprocessing_pipeline": selected_pipeline_name,
        "selected_parameters": selected_parameters,
        "test_metrics": test_metrics,
        "majority_class_baseline_test_metrics": baseline_metrics,
        "error_analysis": {
            "misclassified_count": int(len(misclassified)),
            "false_negatives_attrition_missed": false_negatives,
            "false_positives_false_alerts": false_positives,
            "examples": [
                *[
                    format_error_example(row, "False negative")
                    for row in false_negative_examples
                ],
                *[
                    format_error_example(row, "False positive")
                    for row in false_positive_examples
                ],
            ],
            "details_file": "misclassified_test_cases.csv",
        },
        "limitations": [
            "The model uses only the eight features currently collected by the application.",
            "The dataset is imbalanced; precision and recall should be considered alongside accuracy.",
            "Test metrics describe this dataset and split and do not guarantee performance at another employer.",
            "Risk bands in the application are operational display thresholds, not clinically or statistically validated decision thresholds.",
            "A majority-class baseline can have higher accuracy while detecting no attrition cases.",
            "The feature observation timestamps are not documented; check that model inputs precede the attrition event before interpreting the result as prospective prediction.",
        ],
    }
    _write_json(REPORT_DIR / "evaluation_report.json", evaluation_report)
    _write_experiment_summary(
        REPORT_DIR / "experiment_summary.md",
        eda_report,
        evaluation_report,
    )
    joblib.dump(selected_model, MODEL_PATH)

    print(f"Dataset: {dataset_path}")
    print(f"Rows: {len(data)}; attrition rate: {(target == 1).mean():.2%}")
    print(f"Selected model: {selected_model_name}")
    print(json.dumps(test_metrics, ensure_ascii=False, indent=2))
    print(f"Model saved to: {MODEL_PATH}")
    print(f"Reports and plots saved to: {REPORT_DIR}")
    return evaluation_report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Explore, evaluate, and train the attrition model.")
    parser.add_argument(
        "--data",
        type=Path,
        default=DEFAULT_DATASET,
        help="Path to the lecturer-provided HR attrition CSV.",
    )
    arguments = parser.parse_args()
    train_and_evaluate(arguments.data)
