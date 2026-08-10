from fastapi import APIRouter, Depends, HTTPException, Request

from probuild.api.dependencies import AppContainer
from probuild.api.schemas.generation import ModelInfo

router = APIRouter(prefix="/v1")


def get_container(request: Request) -> AppContainer:
  return request.app.state.container


@router.get("/models", response_model=list[ModelInfo])
def list_models(container: AppContainer = Depends(get_container)) -> list[ModelInfo]:
  return [
    ModelInfo(
      id=model.id,
      version=model.version,
      architecture=model.architecture,
      loaded=container.model_registry.is_available(model.qualified_name),
    )
    for model in container.model_registry.list_models()
  ]


@router.get("/models/{model_id}", response_model=ModelInfo)
def get_model(model_id: str, container: AppContainer = Depends(get_container)) -> ModelInfo:
  try:
    model = container.model_registry.resolve(model_id)
  except KeyError as exc:
    raise HTTPException(status_code=404, detail="model not found") from exc
  return ModelInfo(
    id=model.id,
    version=model.version,
    architecture=model.architecture,
    loaded=container.model_registry.is_available(model.qualified_name),
  )
