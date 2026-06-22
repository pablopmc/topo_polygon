from __future__ import annotations

from typing import Any
from core.reports.pdf_templates.pdf_template_base import PDFTemplate
from core.reports.pdf_templates.A3_landscape import A3LandscapeTemplate
from core.reports.pdf_templates.A4_portrait import A4PortraitTemplate


class PDFTemplateFactory:
    """Factory para gerenciar e fornecer templates de relatórios PDF (Strategy/Factory Patterns)"""

    _templates: dict[str, type[PDFTemplate]] = {
        "A3_LANDSCAPE": A3LandscapeTemplate,
        "A4_PORTRAIT": A4PortraitTemplate,
    }

    @classmethod
    def register_template(cls, template_id: str, template_class: type[PDFTemplate]) -> None:
        """Permite registrar novos templates de relatórios futuramente (ex. A2_landscape, A4_abnt)"""
        cls._templates[template_id.upper()] = template_class

    @classmethod
    def get_template(cls, template_id: str) -> PDFTemplate:
        """Retorna uma instância do template de relatório correspondente"""
        template_class = cls._templates.get(template_id.upper())
        if not template_class:
            raise ValueError(f"Template PDF '{template_id}' não cadastrado no sistema.")
        return template_class()

    @classmethod
    def list_templates(cls) -> list[str]:
        """Retorna a lista de chaves de todos os templates cadastrados"""
        return list(cls._templates.keys())
