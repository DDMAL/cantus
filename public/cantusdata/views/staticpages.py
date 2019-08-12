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
        content = codecs.open(
            os.path.join(settings.BASE_DIR, markdown_file), 
            encoding='utf-8').readlines()
        title_line = content[0]
        the_rest = '\n'.join(content[1:])
        title = re.match(r"^#([A-Za-z0-9 _-]+)$", title_line).group(1)
        content_html = markdown.markdown(the_rest)
        return render(request, 'flatpages/default.html', {'content': content_html, 'title': title})