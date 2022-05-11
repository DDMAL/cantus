# cantus-staticpages
This repository accommodates the content of the static pages in the Cantus Ultimus Website

Currently, the repository accommodates the content of the following static pages:
- [Home Page](content/home.md)
- [About](content/about.md)
- [Activities](content/activities.md)
- [Team](content/team.md)

# General guidelines

There are general guidelines for how this markdown text has to be written so that it is correctly rendered in the Cantus Ultimus website.

- All titles should use an `h1` header tag, more precisely, the equivalent to a `h1` header in `markdown`. For example
```markdown
# This is correct title
```
- Titles should be short (<=30 characters), as they become part of the title and user interface of the website
- Subtitles in the page should use preferrably a `h3` header tag, as this is best rendered by the templates of the website
- All the remaining syntax of markdown will be rendered accordingly (e.g., links to websites, lists, tables, etc.)
- Any text that does not have a particular syntax is considered to be a paragraph (i.e., encoded as a `<p>` tag in the website)

