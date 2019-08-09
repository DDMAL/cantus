from django.shortcuts import render
from django.conf import settings
import markdown
import os.path
import codecs

def homepage(request):
        markdown_file = '../cantus-staticpages/content/home.md'
        content_html = markdown.markdown(
                codecs.open(os.path.join(settings.BASE_DIR, markdown_file),
                encoding='utf-8').read())
        return render(request, 'flatpages/default.html', {'content': content_html, 'title': 'TestTitle'})

def general(request, static_page):
        markdown_file = '../cantus-staticpages/content/{}.md'.format(static_page)
        content_html = markdown.markdown(
                codecs.open(os.path.join(settings.BASE_DIR, markdown_file),
                encoding='utf-8').read())
        return render(request, 'flatpages/default.html', {'content': content_html, 'title': 'TestTitle'})