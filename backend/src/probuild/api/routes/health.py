from fastapi import APIRouter, Depends, Request

from probuild import __version__
from probuild.api.dependencies import AppContainer
from probuild.api.schemas.health import HealthResponse

router = APIRouter(prefix="/v1")


def get_container(request: Request) -> AppContainer:
  return request.app.state.container


@router.get("/health", response_model=HealthResponse)
def health(container: AppContainer = Depends(get_container)) -> HealthResponse:
  loaded = container.model_registry.is_available("probuild-base")
  return HealthResponse(status="ok", version=__version__, model_loaded=loaded)
