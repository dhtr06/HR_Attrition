import os
from pathlib import Path
import joblib
from fastapi import FastAPI, Depends
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from .database import Base, engine, get_db
from .models import Employee, PredictionHistory
from .routers import employees, predictions, dashboard
from .services.employee_importer import import_hr_attrition_csv

# Ensure tables exist
Base.metadata.create_all(bind=engine)

# Import the course dataset into an empty employee directory.
with Session(engine) as db_session:
    emp_count = db_session.scalar(select(func.count(Employee.id)))
    if emp_count == 0:
        imported_count = import_hr_attrition_csv(db_session)
        print(f"[Database] Imported {imported_count} employees from the course dataset.")

app = FastAPI(
    title='TalentPulse AI - HR Attrition Prediction Platform',
    description='Hệ thống phân tích nhân sự và dự đoán rủi ro nghỉ việc bằng Trí tuệ Nhân tạo',
    version='2.0.0'
)

app.include_router(employees.router)
app.include_router(predictions.router)
app.include_router(dashboard.router)

ROOT = Path(__file__).resolve().parent.parent

@app.get('/api/system/status')
def system_status(db: Session = Depends(get_db)):
    model_path = ROOT / 'machine_learning' / 'attrition_model.joblib'
    model_exists = model_path.exists()
    model_algorithm = None
    if model_exists:
        model = joblib.load(model_path)
        classifier = model.named_steps.get('classifier') if hasattr(model, 'named_steps') else model
        model_algorithm = type(classifier).__name__
    db_type = 'MySQL' if 'mysql' in str(engine.url) else 'SQLite (Embedded)'
    emp_count = db.scalar(select(func.count(Employee.id))) or 0
    pred_count = db.scalar(select(func.count(PredictionHistory.id))) or 0

    return {
        'status': 'healthy',
        'app_name': 'TalentPulse AI Platform',
        'version': '2.0.0',
        'database': {
            'type': db_type,
            'connected': True,
            'total_employees': emp_count,
            'total_predictions': pred_count
        },
        'ai_engine': {
            'model_file': 'attrition_model.joblib',
            'model_loaded': model_exists,
            'algorithm': model_algorithm,
            'features': ['age', 'monthly_income', 'years_at_company', 'overtime', 'job_satisfaction', 'work_life_balance', 'department', 'job_role']
        }
    }

app.mount('/static', StaticFiles(directory=ROOT / 'frontend'), name='static')

@app.get('/')
def home():
    return FileResponse(ROOT / 'frontend' / 'index.html')

@app.get('/health')
def health():
    return {'status': 'ok', 'version': '2.0.0'}
