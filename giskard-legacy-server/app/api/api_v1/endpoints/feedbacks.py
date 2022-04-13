from typing import Any, List
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.sql.functions import user

from app import models, schemas
from app import crud
from app.api import deps
from app.core.utils import (
    send_new_feedback_notification,
    send_feedback_reply_notification,
    send_feedback_comment_notification,
)

router = APIRouter()

logger = logging.getLogger("feedback-api")
logger.setLevel(logging.INFO)


@router.post("/{projectId}", response_model=schemas.Msg)
def add_feedback(
    projectId: int,
    feedback_in: schemas.FeedbackCreateSchema,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    project = crud.project.get(db, projectId)
    if (
        crud.user.is_superuser(current_user)
        or project.owner_id == current_user.id
        or current_user.user_id in [u.user_id for u in project.guest_list]
    ):
        feedback = crud.feedback.create(db, feedback_in, current_user.id)
        # send email but not to self
        if current_user.id != project.owner_id:
            project_owner = crud.user.get(db, project.owner_id)
            send_new_feedback_notification(
                project_owner.email,
                current_user.display_name or current_user.user_id,
                project.id,
                project.name,
                feedback.id,
                feedback.feedback_message,
            )
        return schemas.Msg(msg="ok!")
    else:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not enough permissions")


@router.get("/all/{projectId}", response_model=List[schemas.FeedbackSchemaForList])
def get_feedbacks(
    projectId: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    project = crud.project.get(db, projectId)
    
    feedbacks = crud.feedback.get_all_by_project(db, project_id=projectId) if (
        crud.user.is_superuser(current_user)
        or project.owner_id == current_user.id
    ) else crud.feedback.get_by_project_and_user(db, project_id=projectId, user_id=current_user.id) 
    
    return [
        schemas.FeedbackSchemaForList(
            id=f.id,
            user_id=f.user.user_id,
            model_name=f.model.file_name.replace(".pkl.zst", ""),
            dataset_name=f.dataset.file_name.replace(".zst", ""),
            created_on=f.created_on,
            feedback_type=f.feedback_type,
            feature_name=f.feature_name,
            feature_value=f.feature_value,
            feedback_choice=f.feedback_choice,
            feedback_message=f.feedback_message,
        ) for f in feedbacks
    ]


@router.get("/{id}", response_model=schemas.FeedbackSchemaSingle)
def get_feedback(
    id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get a feedback entry by id.
    """
    feedback = crud.feedback.get(db, id=id)
    project = crud.project.get(db, feedback.project_id)
    if (
        crud.user.is_superuser(current_user)
        or project.owner_id == current_user.id
        or feedback.user_id == current_user.id
    ):
        feedback.model.file_name = feedback.model.file_name.replace(".pkl.zst", "")
        feedback.dataset.file_name = feedback.dataset.file_name.replace(".zst", "")
        return feedback
    else:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not enough permissions")


@router.post("/{feedback_id}/reply", response_model=schemas.Msg)
def post_feedback_reply(
    feedback_id: int,
    reply_in: schemas.FeedbackReplyCreateSchema,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:

    feedback = crud.feedback.get(db, id=feedback_id)
    project = crud.project.get(db, feedback.project_id)
    if (
        crud.user.is_superuser(current_user)
        or project.owner_id == current_user.id
        or current_user.user_id in [u.user_id for u in project.guest_list]
    ):
        crud.feedback_reply.create(db, reply_in, feedback.id, current_user.id)
        email_involved_users(reply_in, db, current_user, feedback, project)
        return schemas.Msg(msg="ok!")
    else:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not enough permissions")


def email_involved_users(
    reply_in: schemas.FeedbackReplyCreateSchema,
    db: Session,
    current_user: models.User,
    feedback: models.Feedback,
    project: models.Project,
):
    # but not if self!
    project_owner = crud.user.get(db, feedback.user_id)
    if current_user.id != project_owner.id:
        send_feedback_comment_notification(
            project_owner.email,
            current_user.display_name or current_user.user_id,
            project.id,
            project.name,
            feedback.id,
            reply_in.content,
        )

    # the guy who initialized the feedback
    feedback_owner = crud.user.get(db, feedback.user_id)
    if current_user.id != feedback_owner.id:
        send_feedback_comment_notification(
            feedback_owner.email,
            current_user.display_name or current_user.user_id,
            project.id,
            project.name,
            feedback.id,
            reply_in.content,
        )

    if reply_in.reply_to_reply:
        replying_to_user = crud.feedback_reply.get(db, reply_in.reply_to_reply).user
        if current_user.id != replying_to_user.id:
            send_feedback_reply_notification(
                replying_to_user.email,
                current_user.display_name or current_user.user_id,
                project.id,
                project.name,
                feedback.id,
                reply_in.content,
            )
