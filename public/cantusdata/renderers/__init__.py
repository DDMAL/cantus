from rest_framework.settings import api_settings
from rest_framework.renderers import TemplateHTMLRenderer


class MyHTMLRenderer(TemplateHTMLRenderer):
    def get_template_context(self, *args, **kwargs):
        context = super().get_template_context(*args, **kwargs)
        if isinstance(context, list):
            context = {"items": context}
        return context


templated_view_renderers = (MyHTMLRenderer,) + tuple(
    api_settings.DEFAULT_RENDERER_CLASSES
)
