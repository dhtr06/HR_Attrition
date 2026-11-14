import argparse
from pathlib import Path

import pandas as pd
from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session

from ..database import Base, engine
from ..models import Employee, PredictionHistory


DATASET_PATH = (
    Path(__file__).resolve().parents[2]
    / "machine_learning"
    / "data"
    / "WA_Fn-UseC_-HR-Employee-Attrition.csv"
)
REQUIRED_COLUMNS = {
    "Age",
    "Department",
    "EmployeeNumber",
    "JobRole",
    "JobSatisfaction",
    "MonthlyIncome",
    "OverTime",
    "WorkLifeBalance",
    "YearsAtCompany",
}


def import_hr_attrition_csv(
    db: Session,
    *,
    replace_existing: bool = False,
    dataset_path: Path = DATASET_PATH,
) -> int:
    if not dataset_path.is_file():
        raise FileNotFoundError(f"HR dataset not found: {dataset_path}")

    data = pd.read_csv(dataset_path)
    missing_columns = sorted(REQUIRED_COLUMNS - set(data.columns))
    if missing_columns:
        raise ValueError(f"HR dataset is missing required columns: {missing_columns}")
    if data.empty:
        raise ValueError("HR dataset contains no employee records.")
    if data["EmployeeNumber"].isna().any() or data["EmployeeNumber"].duplicated().any():
        raise ValueError("EmployeeNumber must be present and unique for every CSV row.")

    required_values = [
        "Age",
        "Department",
        "EmployeeNumber",
        "JobRole",
        "JobSatisfaction",
        "MonthlyIncome",
        "OverTime",
        "WorkLifeBalance",
        "YearsAtCompany",
    ]
    if data[required_values].isna().any().any():
        raise ValueError("CSV contains missing values in fields required by the employee directory.")

    current_count = db.scalar(select(func.count(Employee.id))) or 0
    if current_count and not replace_existing:
        raise ValueError(
            f"Database already contains {current_count} employees. "
            "Pass replace_existing=True only when replacement is intended."
        )

    employees = []
    for row in data.to_dict(orient="records"):
        employee_number = int(row["EmployeeNumber"])
        employees.append(
            Employee(
                employee_code=f"CSV-{employee_number:04d}",
                full_name=f"Employee {employee_number:04d}",
                age=int(row["Age"]),
                department=str(row["Department"]),
                job_role=str(row["JobRole"]),
                monthly_income=float(row["MonthlyIncome"]),
                years_at_company=float(row["YearsAtCompany"]),
                overtime=str(row["OverTime"]),
                job_satisfaction=int(row["JobSatisfaction"]),
                work_life_balance=int(row["WorkLifeBalance"]),
            )
        )

    try:
        if replace_existing:
            db.execute(
                update(PredictionHistory)
                .where(PredictionHistory.employee_id.is_not(None))
                .values(employee_id=None)
            )
            db.execute(delete(Employee))
        db.add_all(employees)
        db.flush()
        db.commit()
    except Exception:
        db.rollback()
        raise

    return len(employees)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import HR attrition CSV rows into the application employee directory."
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Replace existing employee records; prediction history is kept but detached.",
    )
    args = parser.parse_args()

    Base.metadata.create_all(bind=engine)
    with Session(engine) as db:
        imported_count = import_hr_attrition_csv(
            db,
            replace_existing=args.replace,
        )
    print(f"Imported {imported_count} employees from {DATASET_PATH}.")


if __name__ == "__main__":
    main()
