import os
from string import Template

HEADER_TEMPLATE_DIRECTORY = "templates/"
BACKBONE_TEMPLATE_DIRECTORY = "templates/underscore-templates/"


def format_underscore_template(name, content):
    """
    Format the template as an Underscore.js template.

    :param name: name of the template
    :param content: content of the template
    :return: string containing formatted template
    """
    return '\n<script type="text/template" id="{0}">\n{1}\n</script>\n'.format(name, content)


def assemble_templates(backbone_template_formatter):
    """
    Assemble the header, the footer, and all backbone templates into one string.

    :param backbone_template_formatter:
    :return: string representing the assembled templates
    """
    # Grab the header content
    base_template = open(os.path.join(HEADER_TEMPLATE_DIRECTORY, "base.html")).read()

    # Attach the backbone templates
    templates = ""
    for f in os.listdir(BACKBONE_TEMPLATE_DIRECTORY):
        if f.endswith(".html"):
            name = f.rstrip(".html")
            content = open(os.path.join(BACKBONE_TEMPLATE_DIRECTORY, f), "r").read()
            # It is a template, so add it
            templates += backbone_template_formatter(name, content)
    return constant_substitution(base_template, {'templates': templates})


def constant_substitution(text, constants_dict=None):
    """
    Substitute some constant in the text.

    :param text:
    :param constants_dict:
    :return:
    """
    if not constants_dict:
        # No constants, so return the same text
        return text
    template = Template(text)
    return template.safe_substitute(constants_dict)


def build_underscore_templates(builddir, constants=None):
    """
    Build the underscore templates and save them to the designated directory.

    :param builddir: path to build directory
    :param constants: dictionary of constants for constant replacement
    :return:
    """
    # Open the file to build
    if not os.path.exists(builddir):
        os.mkdir(builddir)

    output_file = open(os.path.join(builddir, "index.html"), "w+")
    # Get the assembled template string
    assembled_template = assemble_templates(format_underscore_template)
    # Constant replacements
    post_substitution_template = constant_substitution(assembled_template, constants)
    # Write the file content
    output_file.write(post_substitution_template)
    output_file.close()

# Execute
if __name__ == "__main__":
    import sys
    import json

    builddir = sys.argv[1]
    if len(sys.argv) >= 3:
        json_constants = sys.argv[2]
        # Turn the JSON dictionary into a Python dictionary
        python_constants = json.loads(json_constants.replace("'", "\""))
    else:
        # Client did not provide constants
        python_constants = None
    build_underscore_templates(builddir, python_constants)
    print("Templates built successfully!")
