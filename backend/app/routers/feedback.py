from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.errors import AppError
from app.models import Feedback, User
from app.routers.analyses import ERRORS, find_owned_analysis
from app.schemas import FeedbackIn, FeedbackOut
from app.security.auth import get_client_id, get_optional_user

router = APIRouter(tags=["feedback"])


@router.post("/analyses/{analysis_id}/feedback", response_model=FeedbackOut, status_code=201, responses=ERRORS)
def send_feedback(
    analysis_id: str,
    payload: FeedbackIn,
    user: User | None = Depends(get_optional_user),
    client_id: str | None = Depends(get_client_id),
    db: Session = Depends(get_db),
):
    analysis = find_owned_analysis(db, analysis_id, user, client_id)
    if analysis.status != "done":
        raise AppError("analysis_not_finished", "You can rate a result only after the analysis is done", 409)
    true_category = payload.true_category
    if payload.is_correct:
        true_category = analysis.category
    elif true_category is not None and true_category == analysis.category:
        raise AppError("validation_error", "The correct category must differ from the predicted one", 422)
    feedback = None
    if analysis.feedback:
        feedback = analysis.feedback[0]
    if feedback is None:
        feedback = Feedback(analysis_id=analysis.id)
        db.add(feedback)
    feedback.user_id = None
    if user is not None:
        feedback.user_id = user.id
    feedback.is_correct = payload.is_correct
    feedback.true_category = true_category
    feedback.comment = None
    if payload.comment:
        feedback.comment = payload.comment.strip()
    db.commit()
    db.refresh(feedback)
    return FeedbackOut.model_validate(feedback)
