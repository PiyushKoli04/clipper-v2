"""Config API routes."""

from fastapi import APIRouter, Depends
from server.auth import get_current_user
from server.models import ConfigModel
from worker import firestore

router = APIRouter(prefix="/api/config", tags=["config"])


@router.get("", response_model=ConfigModel)
def get_config_endpoint(user: dict = Depends(get_current_user)):
    """Retrieve application configuration from Firestore."""
    data = firestore.get_config()
    return ConfigModel(**data) if data else ConfigModel()


@router.put("", response_model=ConfigModel)
def update_config_endpoint(config: ConfigModel, user: dict = Depends(get_current_user)):
    """Update application configuration in Firestore."""
    data = config.model_dump()
    firestore.set_config(data)
    return config

