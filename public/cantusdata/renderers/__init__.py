from rest_framework.settings import api_settings
from rest_framework.renderers import TemplateHTMLRenderer

templated_view_renderers = (TemplateHTMLRenderer,) + tuple(api_settings.DEFAULT_RENDERER_CLASSES)
