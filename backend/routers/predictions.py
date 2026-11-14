from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, delete
from ..database import get_db
from ..models import PredictionHistory
from ..schemas import PredictionInput
from ..services.predictor import predict

router = APIRouter(prefix='/api/predictions', tags=['Predictions'])

@router.post('')
def run(data: PredictionInput, db: Session = Depends(get_db)):
    try:
        result = predict(data.model_dump())
    except FileNotFoundError as e:
        raise HTTPException(503, str(e))
    except Exception as e:
        raise HTTPException(400, f'Lỗi dự đoán: {e}')

    history_record = PredictionHistory(
        employee_id=data.employee_id,
        probability=result['probability'],
        risk_level=result['risk_level'],
        model_name=result['model_name']
    )
    db.add(history_record)
    db.commit()
    db.refresh(history_record)
    result['id'] = history_record.id
    return result

@router.get('/history')
def history(limit: int = 100, db: Session = Depends(get_db)):
    rows = db.scalars(
        select(PredictionHistory).order_by(PredictionHistory.id.desc()).limit(limit)
    ).all()
    return [{
        'id': x.id,
        'employee_id': x.employee_id,
        'probability': float(x.probability),
        'risk_level': x.risk_level,
        'model_name': x.model_name,
        'created_at': x.created_at.isoformat() if x.created_at else None
    } for x in rows]

@router.delete('/history/{history_id}', status_code=204)
def delete_item(history_id: int, db: Session = Depends(get_db)):
    obj = db.get(PredictionHistory, history_id)
    if not obj:
        raise HTTPException(404, 'Không tìm thấy mục lịch sử')
    db.delete(obj)
    db.commit()
    return None

@router.delete('/history', status_code=200)
def clear_history(db: Session = Depends(get_db)):
    db.execute(delete(PredictionHistory))
    db.commit()
    return {'message': 'Đã xóa toàn bộ lịch sử dự đoán'}
