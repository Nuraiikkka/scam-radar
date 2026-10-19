"""initial tables

Revision ID: 0001_initial
Revises:
Create Date: 2026-10-16 11:08:33.216365

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_admin", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_table(
        "videos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_type", sa.String(length=10), nullable=False),
        sa.Column("source_url", sa.String(length=2048), nullable=True),
        sa.Column("original_filename", sa.String(length=255), nullable=True),
        sa.Column("sha256", sa.String(length=64), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=True),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("stored_path", sa.String(length=1024), nullable=True),
        sa.Column("file_deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_videos_created_at"), "videos", ["created_at"], unique=False)
    op.create_index(op.f("ix_videos_sha256"), "videos", ["sha256"], unique=False)
    op.create_table(
        "analyses",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("client_id", sa.String(length=64), nullable=True),
        sa.Column("video_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=10), nullable=False),
        sa.Column("stage", sa.String(length=20), nullable=False),
        sa.Column("risk_score", sa.Float(), nullable=True),
        sa.Column("category", sa.String(length=30), nullable=True),
        sa.Column("reasons", sa.JSON(), nullable=False),
        sa.Column("transcript", sa.Text(), nullable=True),
        sa.Column("transcript_language", sa.String(length=10), nullable=True),
        sa.Column("ocr_text", sa.Text(), nullable=True),
        sa.Column("links", sa.JSON(), nullable=False),
        sa.Column("phones", sa.JSON(), nullable=False),
        sa.Column("qr_codes", sa.JSON(), nullable=False),
        sa.Column("text_score", sa.Float(), nullable=True),
        sa.Column("vision_score", sa.Float(), nullable=True),
        sa.Column("model_version", sa.String(length=64), nullable=True),
        sa.Column("error_code", sa.String(length=50), nullable=True),
        sa.Column("error_message", sa.String(length=500), nullable=True),
        sa.Column("processing_seconds", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["video_id"], ["videos.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_analyses_category"), "analyses", ["category"], unique=False)
    op.create_index("ix_analyses_client_created", "analyses", ["client_id", "created_at"], unique=False)
    op.create_index(op.f("ix_analyses_created_at"), "analyses", ["created_at"], unique=False)
    op.create_index(op.f("ix_analyses_risk_score"), "analyses", ["risk_score"], unique=False)
    op.create_index(op.f("ix_analyses_status"), "analyses", ["status"], unique=False)
    op.create_index("ix_analyses_user_created", "analyses", ["user_id", "created_at"], unique=False)
    op.create_index(op.f("ix_analyses_video_id"), "analyses", ["video_id"], unique=False)
    op.create_table(
        "feedback",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("analysis_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.Column("true_category", sa.String(length=30), nullable=True),
        sa.Column("comment", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["analysis_id"], ["analyses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("analysis_id"),
    )
    op.create_index(op.f("ix_feedback_created_at"), "feedback", ["created_at"], unique=False)
    op.create_table(
        "signals",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("analysis_id", sa.String(length=36), nullable=False),
        sa.Column("source", sa.String(length=20), nullable=False),
        sa.Column("kind", sa.String(length=30), nullable=False),
        sa.Column("value", sa.String(length=500), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["analysis_id"], ["analyses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_signals_analysis_id"), "signals", ["analysis_id"], unique=False)
    op.create_index(op.f("ix_signals_kind"), "signals", ["kind"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_signals_kind"), table_name="signals")
    op.drop_index(op.f("ix_signals_analysis_id"), table_name="signals")
    op.drop_table("signals")
    op.drop_index(op.f("ix_feedback_created_at"), table_name="feedback")
    op.drop_table("feedback")
    op.drop_index(op.f("ix_analyses_video_id"), table_name="analyses")
    op.drop_index("ix_analyses_user_created", table_name="analyses")
    op.drop_index(op.f("ix_analyses_status"), table_name="analyses")
    op.drop_index(op.f("ix_analyses_risk_score"), table_name="analyses")
    op.drop_index(op.f("ix_analyses_created_at"), table_name="analyses")
    op.drop_index("ix_analyses_client_created", table_name="analyses")
    op.drop_index(op.f("ix_analyses_category"), table_name="analyses")
    op.drop_table("analyses")
    op.drop_index(op.f("ix_videos_sha256"), table_name="videos")
    op.drop_index(op.f("ix_videos_created_at"), table_name="videos")
    op.drop_table("videos")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
