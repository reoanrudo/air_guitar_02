from django.views.generic import TemplateView


class IndexView(TemplateView):
    """ランディングページビュー"""

    template_name = "core/index.html"
