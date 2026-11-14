from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from ..database import get_db
from ..models import Employee, PredictionHistory

router = APIRouter(prefix='/api/dashboard', tags=['Dashboard'])

@router.get('/summary')
def summary(db: Session = Depends(get_db)):
    employees = db.scalars(select(Employee)).all()
    predictions = db.scalars(select(PredictionHistory).order_by(PredictionHistory.id.desc())).all()

    total_emp = len(employees)
    total_pred = len(predictions)

    high_risk_pred = sum(1 for p in predictions if p.risk_level == 'Cao')
    med_risk_pred = sum(1 for p in predictions if p.risk_level == 'Trung bình')
    low_risk_pred = sum(1 for p in predictions if p.risk_level == 'Thấp')

    avg_sat = round(sum(e.job_satisfaction or 0 for e in employees) / total_emp, 1) if total_emp else 0
    avg_wlb = round(sum(e.work_life_balance or 0 for e in employees) / total_emp, 1) if total_emp else 0
    avg_income = round(sum(float(e.monthly_income or 0) for e in employees) / total_emp, 0) if total_emp else 0
    ot_count = sum(1 for e in employees if (e.overtime or '').lower() == 'yes')
    ot_rate = round((ot_count / total_emp) * 100, 1) if total_emp else 0

    # Department breakdown
    dept_map = {}
    for e in employees:
        d = e.department or 'Khác'
        if d not in dept_map:
            dept_map[d] = {'department': d, 'count': 0, 'total_income': 0, 'ot_count': 0, 'low_sat_count': 0}
        dept_map[d]['count'] += 1
        dept_map[d]['total_income'] += float(e.monthly_income or 0)
        if (e.overtime or '').lower() == 'yes':
            dept_map[d]['ot_count'] += 1
        if (e.job_satisfaction or 3) <= 2:
            dept_map[d]['low_sat_count'] += 1

    dept_stats = []
    for d, val in dept_map.items():
        cnt = val['count']
        dept_stats.append({
            'department': d,
            'count': cnt,
            'avg_income': round(val['total_income'] / cnt, 0) if cnt else 0,
            'ot_count': val['ot_count'],
            'low_sat_count': val['low_sat_count']
        })

    # High attention candidates (employees with OT = Yes and low satisfaction)
    attention_list = []
    for e in employees:
        score = 0
        if (e.overtime or '').lower() == 'yes':
            score += 2
        if (e.job_satisfaction or 3) <= 2:
            score += 2
        if (e.work_life_balance or 3) <= 2:
            score += 1
        if score >= 3:
            attention_list.append({
                'id': e.id,
                'employee_code': e.employee_code,
                'full_name': e.full_name,
                'department': e.department,
                'job_role': e.job_role,
                'monthly_income': float(e.monthly_income or 0),
                'years_at_company': float(e.years_at_company or 0),
                'overtime': e.overtime,
                'job_satisfaction': e.job_satisfaction,
                'work_life_balance': e.work_life_balance,
                'reason': 'Làm OT và hài lòng thấp' if (e.overtime or '').lower() == 'yes' and (e.job_satisfaction or 3) <= 2 else 'Cần chú ý giữ chân'
            })

    return {
        'total_employees': total_emp,
        'total_predictions': total_pred,
        'high_risk_predictions': high_risk_pred,
        'medium_risk_predictions': med_risk_pred,
        'low_risk_predictions': low_risk_pred,
        'avg_satisfaction': avg_sat,
        'avg_wlb': avg_wlb,
        'avg_income': avg_income,
        'ot_rate': ot_rate,
        'departments': dept_stats,
        'attention_list': attention_list[:6]
    }
