from typing import List

from django.apps import apps
from django.db.models import ManyToOneRel
from django.db.models.base import ModelBase


def get_project_models() -> List:
    all_models = apps.get_models()

    project_models = [
        model for model in all_models
    ]

    return project_models


def get_model_fields(model: ModelBase) -> List:
    meta = getattr(model, "_meta")

    fields = []

    for field in meta.get_fields():
        if isinstance(field, ManyToOneRel):
            continue
        fields.append(field)

    fields.sort(key=lambda _f: "" if _f.name == "id" else _f.name)

    return fields
