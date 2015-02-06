import os

BUILD_DIRECTORY = "build/"
HEADER_TEMPLATE_DIRECTORY = "templates/"
BACKBONE_TEMPLATE_DIRECTORY = "templates/underscore-templates/"

def format_underscore_template(name, content):
	"""
	Format the template as an Underscore.js template.
	"""
	return '\n<script type="text/template" id="{0}">\n{1}\n</script>\n'.format(name, content)

def assemble_templates(backbone_template_formatter):
	"""
	Assemble the header, the footer, and all backbone templates into one string.
	"""
	# Grab the header content
	output = open(HEADER_TEMPLATE_DIRECTORY + "header.html").read()
	# Attach the backbone templates
	for file in os.listdir(BACKBONE_TEMPLATE_DIRECTORY):
	    if file.endswith(".html"):
	    	name = file.rstrip(".html")
	    	content = open(BACKBONE_TEMPLATE_DIRECTORY + file, "r").read()
	        # It is a template, so add it
	        output += backbone_template_formatter(name, content)
	# Append the footer content
	output += open(HEADER_TEMPLATE_DIRECTORY + "footer.html", 'r').read()
	return output

def build_underscore_templates():
	# Open the file to build
	file = open(BUILD_DIRECTORY + "index.html", "w+")
	# Get and write it's content
	file.write(assemble_templates(format_underscore_template))
	file.close()

# Execute
build_underscore_templates();
print "Templates built successfully!"
