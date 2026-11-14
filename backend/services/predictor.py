import os
from pathlib import Path
import joblib
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

def analyze_factors(payload: dict, probability: float):
    factors = []
    recommendations = []

    overtime = str(payload.get('overtime', '')).strip().lower() == 'yes'
    satisfaction = payload.get('job_satisfaction', 3)
    wlb = payload.get('work_life_balance', 3)
    income = payload.get('monthly_income', 5000)
    years = payload.get('years_at_company', 3)
    age = payload.get('age', 30)
    role = payload.get('job_role', 'Nhân viên')

    # Analyze key drivers
    if overtime:
        factors.append({
            'icon': 'flame',
            'title': 'Làm thêm giờ thường xuyên (Overtime = Yes)',
            'desc': 'Áp lực tăng ca liên tục làm tăng nguy cơ kiệt sức (burnout) và giảm mức độ gắn bó dài hạn.',
            'impact': 'high'
        })
        recommendations.append('Rà soát lại khối lượng công việc, hạn chế làm thêm ngoài giờ và có chế độ bù nghỉ hợp lý.')

    if satisfaction is not None and satisfaction <= 2:
        factors.append({
            'icon': 'frown',
            'title': f'Mức độ hài lòng công việc thấp ({satisfaction}/4)',
            'desc': 'Điểm số khảo sát phản ánh tâm lý chưa thoải mái với vai trò, văn hóa đội ngũ hoặc lãnh đạo.',
            'impact': 'high'
        })
        recommendations.append('HR và Trưởng bộ phận cần tổ chức buổi phỏng vấn 1-1 (Stay Interview) để thấu hiểu các vướng mắc cá nhân.')
    elif satisfaction is not None and satisfaction >= 4:
        factors.append({
            'icon': 'smile',
            'title': f'Mức độ hài lòng công việc xuất sắc ({satisfaction}/4)',
            'desc': 'Yếu tố tích cực giữ chân nhân sự gắn bó với văn hóa và tổ chức.',
            'impact': 'positive'
        })

    if wlb is not None and wlb <= 2:
        factors.append({
            'icon': 'scale',
            'title': f'Mất cân bằng công việc & cuộc sống ({wlb}/4)',
            'desc': 'Cân bằng WLB thấp là một trong những nguyên nhân hàng đầu khiến nhân tài chuyển việc.',
            'impact': 'medium'
        })
        recommendations.append('Áp dụng chính sách làm việc linh hoạt (hybrid/remote) hoặc hỗ trợ chăm sóc sức khỏe tinh thần.')

    if income is not None:
        if income < 3500 and years > 2:
            factors.append({
                'icon': 'dollar',
                'title': f'Thu nhập ${income:,.0f} chưa tương xứng với thâm niên {years} năm',
                'desc': 'Chênh lệch mức đãi ngộ so với mặt bằng thị trường tạo động lực tìm kiếm cơ hội mới.',
                'impact': 'high'
            })
            recommendations.append(f'Xem xét đánh giá lại mức lương và lộ trình thăng tiến cho vị trí {role} trong kỳ xét duyệt gần nhất.')
        elif income >= 8000:
            factors.append({
                'icon': 'dollar',
                'title': f'Mức thu nhập đãi ngộ cạnh tranh (${income:,.0f}/tháng)',
                'desc': 'Gói đãi ngộ tốt là điểm tựa giữ chân nhân sự chủ chốt.',
                'impact': 'positive'
            })

    if years is not None and years <= 1.5:
        factors.append({
            'icon': 'clock',
            'title': f'Nhân sự mới gia nhập ({years} năm thâm niên)',
            'desc': 'Giai đoạn thử thách hòa nhập văn hóa (onboarding phase) có tỷ lệ biến động tự nhiên cao.',
            'impact': 'medium'
        })
        recommendations.append('Chỉ định người hướng dẫn (mentor/buddy) để hỗ trợ hòa nhập chuyên môn và tinh thần đội ngũ.')

    if not recommendations:
        recommendations.append('Duy trì các chính sách ghi nhận thành tích, đào tạo nâng cao kỹ năng và môi trường làm việc cởi mở.')
        recommendations.append('Khảo sát định kỳ mức độ hài lòng (eNPS) để chủ động phát hiện sớm tâm tư nhân viên.')

    return factors, recommendations

def predict(payload: dict):
    model_path = os.getenv('MODEL_PATH', str(BASE_DIR / 'machine_learning' / 'attrition_model.joblib'))
    
    probability = None
    model_name = 'Scikit-Learn Random Forest Pipeline'

    if os.path.exists(model_path):
        try:
            model = joblib.load(model_path)
            # Ensure payload matches required columns
            df_input = pd.DataFrame([{
                'age': int(payload.get('age', 30)),
                'monthly_income': float(payload.get('monthly_income', 5000)),
                'years_at_company': float(payload.get('years_at_company', 3)),
                'overtime': str(payload.get('overtime', 'No')),
                'job_satisfaction': int(payload.get('job_satisfaction', 3)),
                'work_life_balance': int(payload.get('work_life_balance', 3)),
                'department': str(payload.get('department', 'Sales')),
                'job_role': str(payload.get('job_role', 'Sales Executive'))
            }])
            if hasattr(model, 'predict_proba'):
                proba = model.predict_proba(df_input)[0]
                probability = float(proba[1])
                model_name = f"{type(model).__name__} (attrition_model.joblib)"
        except Exception as e:
            print(f"Warning: Could not predict with joblib model: {e}")

    # Fallback to intelligent HR Bayesian heuristic if model wasn't loaded
    if probability is None:
        model_name = 'TalentRetention Heuristic AI Engine'
        base_score = 0.20
        if str(payload.get('overtime', '')).lower() == 'yes':
            base_score += 0.28
        sat = payload.get('job_satisfaction', 3)
        base_score += (2.5 - sat) * 0.12
        wlb = payload.get('work_life_balance', 3)
        base_score += (2.5 - wlb) * 0.08
        income = payload.get('monthly_income', 5000)
        if income < 4000:
            base_score += 0.14
        elif income > 10000:
            base_score -= 0.12
        years = payload.get('years_at_company', 3)
        if years < 2:
            base_score += 0.08
        probability = max(0.02, min(0.98, base_score))

    probability = round(probability, 4)

    if probability >= 0.65:
        risk_level = 'Cao'
        risk_color = '#ef4444'
        risk_badge = 'High Risk'
    elif probability >= 0.35:
        risk_level = 'Trung bình'
        risk_color = '#f59e0b'
        risk_badge = 'Medium Risk'
    else:
        risk_level = 'Thấp'
        risk_color = '#10b981'
        risk_badge = 'Low Risk'

    factors, recommendations = analyze_factors(payload, probability)

    return {
        'probability': probability,
        'risk_level': risk_level,
        'risk_color': risk_color,
        'risk_badge': risk_badge,
        'model_name': model_name,
        'key_factors': factors,
        'recommendations': recommendations,
        'notice': 'Dự báo thống kê hỗ trợ quyết định quản trị nhân sự, không thay thế đánh giá toàn diện của con người.'
    }
