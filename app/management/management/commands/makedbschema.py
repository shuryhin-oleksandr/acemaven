import os
from pathlib import Path

from django.core.management.base import BaseCommand
from django.template.loader import get_template

from app.core.util.models_utils import get_project_models, get_model_fields

_this_file = Path(__file__).resolve()
DIR_MANAGEMENT = _this_file.parent.parent.parent
DIR_SCHEMAS = DIR_MANAGEMENT / 'schemas'


class Command(BaseCommand):
    help = "Generates a database schema according to current models (install graphviz before start)"

    def handle(self, *args, **options):
        template = get_template("/management/schema.gv.jinja2")
        context = dict(
            models=get_project_models(),
            fields=get_model_fields,
            color=get_color_for_field,
        )
        schema = template.render(context)
        schema_name = "database-schema"
        schema_pdf = (DIR_SCHEMAS / f"{schema_name}.pdf").resolve()
        schema_gv = (DIR_SCHEMAS / f"{schema_name}.gv").resolve()

        with schema_gv.open("w") as dst:
            dst.write(schema)

        os.system(f"dot -Tpdf '{schema_gv.as_posix()}' -o '{schema_pdf.as_posix()}'")
        os.system(f"open '{schema_pdf.as_posix()}'")


def get_color_for_field(field) -> str:
    if field.null:
        return "#808080"

    if field.primary_key:
        return "#0000ff"

    return "#000000"
