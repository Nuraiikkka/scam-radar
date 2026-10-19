from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

Category = Literal["investment_platform", "pyramid", "betting", "giveaway", "job_offer", "none"]
Status = Literal["queued", "running", "done", "failed"]
Stage = Literal["queued", "downloading", "listening", "reading_screen", "scoring", "finished"]
ReasonSource = Literal["speech", "screen_text", "qr", "rule", "classifier"]


class ErrorBody(BaseModel):
    code: str
    message: str
    request_id: str | None = None


class ErrorOut(BaseModel):
    error: ErrorBody


class Reason(BaseModel):
    source: ReasonSource
    code: str
    message_en: str
    message_ru: str


class AnalyzeUrlIn(BaseModel):
    url: str = Field(min_length=10, max_length=2048)


class AnalyzeCreated(BaseModel):
    analysis_id: str
    status: Status


class FeedbackIn(BaseModel):
    is_correct: bool
    true_category: Category | None = None
    comment: str | None = Field(default=None, max_length=500)


class FeedbackOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    is_correct: bool
    true_category: Category | None
    comment: str | None
    created_at: datetime


class AnalysisOut(BaseModel):
    id: str
    status: Status
    stage: Stage
    risk_score: float | None
    category: Category | None
    reasons: list[Reason]
    transcript: str | None
    transcript_language: str | None
    ocr_text: str | None
    links: list[str]
    phones: list[str]
    qr_codes: list[str]
    source_type: Literal["url", "upload"]
    source_url: str | None
    original_filename: str | None
    model_version: str | None
    error_code: str | None
    error_message: str | None
    processing_seconds: float | None
    created_at: datetime
    finished_at: datetime | None
    feedback: FeedbackOut | None


class AnalysisSummary(BaseModel):
    id: str
    status: Status
    risk_score: float | None
    category: Category | None
    source_type: Literal["url", "upload"]
    source_url: str | None
    original_filename: str | None
    created_at: datetime


class AnalysisPage(BaseModel):
    items: list[AnalysisSummary]
    total: int
    page: int
    page_size: int


class DeletedOut(BaseModel):
    deleted: int


class CategoryCount(BaseModel):
    category: Category
    count: int


class DailyRisk(BaseModel):
    day: date
    count: int
    average_risk: float


class StatsOut(BaseModel):
    total_analyses: int
    done_analyses: int
    failed_analyses: int
    scam_share: float
    average_processing_seconds: float | None
    per_category: list[CategoryCount]
    risk_over_time: list[DailyRisk]


class HealthOut(BaseModel):
    status: Literal["ok", "degraded"]
    database: bool
    redis: bool
    worker: bool
    version: str


class CategoryOut(BaseModel):
    id: Category
    name_en: str
    name_ru: str
    description_en: str
    description_ru: str


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class RefreshIn(BaseModel):
    refresh_token: str = Field(min_length=10, max_length=2048)


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"]
    expires_in: int


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    is_admin: bool
    created_at: datetime
