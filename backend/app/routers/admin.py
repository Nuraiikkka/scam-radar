import csv
import io

from fastapi import APIRouter, Depends, FastAPI, Request
from fastapi.responses import StreamingResponse
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import SessionLocal, engine, get_db
from app.models import Analysis, Feedback, Signal, User, Video
from app.security.auth import require_admin, verify_password
from app.settings.conf import settings

router = APIRouter(prefix="/admin", tags=["admin"])


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        email = str(form.get("username", "")).lower().strip()
        password = str(form.get("password", ""))
        db = SessionLocal()
        try:
            user = db.scalar(select(User).where(User.email == email))
            if user is None or not user.is_admin or not user.is_active:
                return False
            if not verify_password(password, user.password_hash):
                return False
            request.session.update({"admin_user_id": user.id})
            return True
        finally:
            db.close()

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        user_id = request.session.get("admin_user_id")
        if user_id is None:
            return False
        db = SessionLocal()
        try:
            user = db.get(User, user_id)
            return user is not None and user.is_admin and user.is_active
        finally:
            db.close()


class UserAdmin(ModelView, model=User):
    name = "User"
    name_plural = "Users"
    column_list = [User.id, User.email, User.is_admin, User.is_active, User.created_at]
    column_searchable_list = [User.email]
    form_excluded_columns = [User.password_hash, User.analyses]
    can_create = False
    icon = "fa-solid fa-user"


class VideoAdmin(ModelView, model=Video):
    name = "Video"
    name_plural = "Videos"
    column_list = [
        Video.id,
        Video.source_type,
        Video.source_url,
        Video.original_filename,
        Video.duration_seconds,
        Video.file_deleted_at,
        Video.created_at,
    ]
    can_create = False
    can_edit = False
    icon = "fa-solid fa-film"


class AnalysisAdmin(ModelView, model=Analysis):
    name = "Analysis"
    name_plural = "Analyses"
    column_list = [
        Analysis.id,
        Analysis.status,
        Analysis.category,
        Analysis.risk_score,
        Analysis.error_code,
        Analysis.model_version,
        Analysis.created_at,
    ]
    column_sortable_list = [Analysis.created_at, Analysis.risk_score]
    column_searchable_list = [Analysis.id, Analysis.category]
    can_create = False
    can_edit = False
    icon = "fa-solid fa-magnifying-glass"


class SignalAdmin(ModelView, model=Signal):
    name = "Signal"
    name_plural = "Signals"
    column_list = [Signal.id, Signal.analysis_id, Signal.source, Signal.kind, Signal.value, Signal.weight]
    column_searchable_list = [Signal.kind, Signal.value]
    can_create = False
    can_edit = False
    icon = "fa-solid fa-flag"


class FeedbackAdmin(ModelView, model=Feedback):
    name = "Feedback"
    name_plural = "Feedback"
    column_list = [
        Feedback.id,
        Feedback.analysis_id,
        Feedback.is_correct,
        Feedback.true_category,
        Feedback.comment,
        Feedback.created_at,
    ]
    can_create = False
    can_export = True
    export_types = ["csv"]
    icon = "fa-solid fa-comment"


def setup_admin(app: FastAPI) -> None:
    backend = AdminAuth(secret_key=settings.secret_key)
    admin = Admin(app, engine, authentication_backend=backend, title="Scam Radar Admin", base_url="/admin")
    admin.add_view(UserAdmin)
    admin.add_view(VideoAdmin)
    admin.add_view(AnalysisAdmin)
    admin.add_view(SignalAdmin)
    admin.add_view(FeedbackAdmin)


def feedback_text(analysis: Analysis) -> str:
    parts = []
    if analysis.transcript:
        parts.append(analysis.transcript)
    if analysis.ocr_text:
        parts.append(analysis.ocr_text)
    return " ".join(parts).replace("\n", " ").strip()


def build_feedback_csv(db: Session) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["text", "category", "source", "lang", "predicted", "is_correct", "analysis_id"])
    query = select(Feedback).order_by(Feedback.created_at)
    for feedback in db.scalars(query):
        analysis = feedback.analysis
        text = feedback_text(analysis)
        if not text or not feedback.true_category:
            continue
        language = ""
        if analysis.transcript_language:
            language = analysis.transcript_language
        predicted = ""
        if analysis.category:
            predicted = analysis.category
        is_correct = "0"
        if feedback.is_correct:
            is_correct = "1"
        writer.writerow([text, feedback.true_category, "feedback", language, predicted, is_correct, analysis.id])
    return buffer.getvalue()


@router.get("/feedback.csv", response_class=StreamingResponse)
def export_feedback(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    content = build_feedback_csv(db)
    headers = {"Content-Disposition": "attachment; filename=feedback.csv"}
    return StreamingResponse(iter([content]), media_type="text/csv; charset=utf-8", headers=headers)
