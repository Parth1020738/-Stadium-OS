"""add_ai_models

Revision ID: dbb8a259bb54
Revises: 8c0d1e413ef4
Create Date: 2026-07-12 22:19:28.984542

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'dbb8a259bb54'
down_revision: Union[str, None] = '8c0d1e413ef4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. ai_explanations
    op.create_table(
        "ai_explanations",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("evidence", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False, default=0.0),
        sa.Column("related_events", sa.JSON(), nullable=True),
        sa.Column("playbooks", sa.JSON(), nullable=True),
        sa.Column("risks", sa.JSON(), nullable=True),
        sa.Column("alternatives", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, default=False),
        sa.Column("version_id", sa.Integer(), nullable=False, default=1)
    )

    # 2. ai_recommendations
    op.create_table(
        "ai_recommendations",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True),
        sa.Column("recommendation_type", sa.String(length=100), nullable=False),
        sa.Column("recommendation", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, default=0.0),
        sa.Column("priority", sa.String(length=50), nullable=False, default="Medium"),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("affected_services", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, default="Proposed"),
        sa.Column("explanation_id", sa.Integer(), sa.ForeignKey("ai_explanations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("suggested_commands", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, default=False),
        sa.Column("version_id", sa.Integer(), nullable=False, default=1)
    )

    # 3. ai_risk_assessments
    op.create_table(
        "ai_risk_assessments",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True),
        sa.Column("crowd_risk", sa.Float(), nullable=True, default=0.0),
        sa.Column("medical_risk", sa.Float(), nullable=True, default=0.0),
        sa.Column("security_risk", sa.Float(), nullable=True, default=0.0),
        sa.Column("fire_risk", sa.Float(), nullable=True, default=0.0),
        sa.Column("transit_risk", sa.Float(), nullable=True, default=0.0),
        sa.Column("accessibility_risk", sa.Float(), nullable=True, default=0.0),
        sa.Column("overall_risk", sa.Float(), nullable=True, default=0.0),
        sa.Column("status", sa.String(length=50), nullable=False, default="LOW"),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("contributing_factors", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, default=False),
        sa.Column("version_id", sa.Integer(), nullable=False, default=1)
    )

    # 4. ai_decisions
    op.create_table(
        "ai_decisions",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True),
        sa.Column("recommendation_id", sa.Integer(), sa.ForeignKey("ai_recommendations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("decision_type", sa.String(length=50), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("operator_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, default=False),
        sa.Column("version_id", sa.Integer(), nullable=False, default=1)
    )

    # 5. ai_correlations
    op.create_table(
        "ai_correlations",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True),
        sa.Column("source_service", sa.String(length=100), nullable=False),
        sa.Column("target_service", sa.String(length=100), nullable=False),
        sa.Column("correlation_type", sa.String(length=100), nullable=False),
        sa.Column("strength", sa.Float(), nullable=True, default=0.0),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, default=False),
        sa.Column("version_id", sa.Integer(), nullable=False, default=1)
    )

    # 6. ai_feedbacks
    op.create_table(
        "ai_feedbacks",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True),
        sa.Column("recommendation_id", sa.Integer(), sa.ForeignKey("ai_recommendations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comments", sa.Text(), nullable=True),
        sa.Column("operator_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, default=False),
        sa.Column("version_id", sa.Integer(), nullable=False, default=1)
    )

    # 7. ai_timeline
    op.create_table(
        "ai_timeline",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, default=False),
        sa.Column("version_id", sa.Integer(), nullable=False, default=1)
    )

    # 8. ai_audits
    op.create_table(
        "ai_audits",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(length=255), nullable=False),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, default=False),
        sa.Column("version_id", sa.Integer(), nullable=False, default=1)
    )

    # 9. ai_knowledge_references
    op.create_table(
        "ai_knowledge_references",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True),
        sa.Column("recommendation_id", sa.Integer(), sa.ForeignKey("ai_recommendations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("citation_label", sa.String(length=255), nullable=False),
        sa.Column("reference_url", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, default=False),
        sa.Column("version_id", sa.Integer(), nullable=False, default=1)
    )


def downgrade() -> None:
    op.drop_table("ai_knowledge_references")
    op.drop_table("ai_audits")
    op.drop_table("ai_timeline")
    op.drop_table("ai_feedbacks")
    op.drop_table("ai_correlations")
    op.drop_table("ai_decisions")
    op.drop_table("ai_risk_assessments")
    op.drop_table("ai_recommendations")
    op.drop_table("ai_explanations")
