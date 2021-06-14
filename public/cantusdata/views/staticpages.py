from django.shortcuts import render
from django.conf import settings
import markdown
import re
import codecs


def homepage(request):
    """The view of the homepage, generated from a Markdown file.

    The content is taken from a Markdown file,
    which is always located at `home.md` of the `cantus-staticpages` repository.
    """
    markdown_file = "cantus-staticpages/content/home.md"
    markdown_fullpath = settings.BASE_DIR.parent / markdown_file
    content = codecs.open(markdown_fullpath, encoding="utf-8").read()
    content_as_html = markdown.markdown(content)
    context = {"content": content_as_html}
    return render(request, "staticpages/homepage.html", context)


def general(request, static_page):
    """The view of a generic static page generated from a Markdown file.

    The first line of the markdown is considered the title.
    The rest of the markdown is considered the content.

    Parameters
    ----------
    static_page : str
        Name of the markdown file where the content is to be found,
        which is extracted from the url of the staticpage in `urls.py`
    """
    markdown_file = f"cantus-staticpages/content/{static_page}.md"
    mrkdwn_fullpath = settings.BASE_DIR.parent / markdown_file
    titlecont = codecs.open(mrkdwn_fullpath, encoding="utf-8").readlines()
    title_line = titlecont[0]
    content = "".join(titlecont[1:])
    title = re.match(r"^#([A-Za-z0-9 _-]+)$", title_line).group(1)
    content_as_html = markdown.markdown(content, extensions=["tables"])
    context = {"title": title, "content": content_as_html}
    return render(request, "staticpages/general.html", context)

def about(request):
    return general(request, "about")

def team(request):
    return general(request, "team")

def activities(request):
    return general(request, "activities")

def manifests(request):
    return general(request, "manifests")
