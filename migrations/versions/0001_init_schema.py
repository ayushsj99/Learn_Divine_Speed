"""init schema

Revision ID: 0001
Revises:
Create Date: 2026-06-25
"""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    op.create_table(
        "users",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True,
                   server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False,
                   server_default=sa.text("now()")),
    )

    op.create_table(
        "syllabi",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True,
                   server_default=sa.text("gen_random_uuid()")),
        sa.Column("session_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("framework", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False,
                   server_default=sa.text("now()")),
    )

    op.create_table(
        "sessions",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True,
                   server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.dialects.postgresql.UUID(as_uuid=True),
                   sa.ForeignKey("users.id"), nullable=False),
        # framework/goal are always supplied by the user at intake — never hardcoded.
        sa.Column("framework", sa.Text(), nullable=False),
        sa.Column("framework_version", sa.Text(), nullable=True),
        sa.Column("goal", sa.Text(), nullable=False),
        sa.Column("goal_context", sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column("level", sa.Text(), nullable=True),
        sa.Column("syllabus_id", sa.dialects.postgresql.UUID(as_uuid=True),
                   sa.ForeignKey("syllabi.id"), nullable=True),
        sa.Column("current_concept_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("phase", sa.Text(), nullable=False, server_default="intake"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False,
                   server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False,
                   server_default=sa.text("now()")),
    )
    op.create_foreign_key(
        "fk_syllabi_session", "syllabi", "sessions", ["session_id"], ["id"],
    )

    op.create_table(
        "syllabus_concepts",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True,
                   server_default=sa.text("gen_random_uuid()")),
        sa.Column("syllabus_id", sa.dialects.postgresql.UUID(as_uuid=True),
                   sa.ForeignKey("syllabi.id"), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("prereq_concept_ids", sa.dialects.postgresql.ARRAY(sa.dialects.postgresql.UUID(as_uuid=True)),
                   nullable=False, server_default="{}"),
        sa.Column("difficulty", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="pending"),
    )
    op.create_foreign_key(
        "fk_sessions_current_concept", "sessions", "syllabus_concepts",
        ["current_concept_id"], ["id"],
    )

    op.create_table(
        "mastery_entries",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True,
                   server_default=sa.text("gen_random_uuid()")),
        sa.Column("session_id", sa.dialects.postgresql.UUID(as_uuid=True),
                   sa.ForeignKey("sessions.id"), nullable=False),
        sa.Column("concept_id", sa.dialects.postgresql.UUID(as_uuid=True),
                   sa.ForeignKey("syllabus_concepts.id"), nullable=False),
        sa.Column("mastery_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("shaky_flag", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("last_reinforced_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False,
                   server_default=sa.text("now()")),
        sa.UniqueConstraint("session_id", "concept_id", name="uq_mastery_session_concept"),
    )

    op.create_table(
        "diagnostic_responses",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True,
                   server_default=sa.text("gen_random_uuid()")),
        sa.Column("session_id", sa.dialects.postgresql.UUID(as_uuid=True),
                   sa.ForeignKey("sessions.id"), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=True),
        sa.Column("correct", sa.Boolean(), nullable=True),
        sa.Column("asked_at", sa.TIMESTAMP(timezone=True), nullable=False,
                   server_default=sa.text("now()")),
    )

    op.create_table(
        "submissions",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True,
                   server_default=sa.text("gen_random_uuid()")),
        sa.Column("session_id", sa.dialects.postgresql.UUID(as_uuid=True),
                   sa.ForeignKey("sessions.id"), nullable=False),
        sa.Column("concept_id", sa.dialects.postgresql.UUID(as_uuid=True),
                   sa.ForeignKey("syllabus_concepts.id"), nullable=False),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("result_status", sa.Text(), nullable=False),
        sa.Column("stdout", sa.Text(), nullable=True),
        sa.Column("stderr", sa.Text(), nullable=True),
        sa.Column("hint_given", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False,
                   server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("submissions")
    op.drop_table("diagnostic_responses")
    op.drop_table("mastery_entries")
    op.drop_constraint("fk_sessions_current_concept", "sessions", type_="foreignkey")
    op.drop_table("syllabus_concepts")
    op.drop_constraint("fk_syllabi_session", "syllabi", type_="foreignkey")
    op.drop_table("sessions")
    op.drop_table("syllabi")
    op.drop_table("users")
