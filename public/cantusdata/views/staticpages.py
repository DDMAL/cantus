from django.shortcuts import render
from django.conf import settings
import markdown
import os.path
import re
import codecs

def homepage(request):
        markdown_file = '../cantus-staticpages/content/home.md'
        content = codecs.open(os.path.join(settings.BASE_DIR, markdown_file), 
            encoding='utf-8').read()
        content_html = markdown.markdown(content)
        return render(request, 'flatpages/default.html', {'content': content_html, 'title': ''})

def general(request, static_page):
        markdown_file = '../cantus-staticpages/content/{}.md'.format(static_page)
        content = codecs.open(os.path.join(settings.BASE_DIR, markdown_file), 
            encoding='utf-8').read()
        title = re.match(r"^#([A-Za-z0-9 _-]+)", content)
        content_html = markdown.markdown(content)
        return render(request, 'flatpages/default.html', {'content': content_html, 'title': title})