def show_attributes(attributes):
	for i in range(attributes.length):
		item = attributes.item(i)
		print item.name + "='" + item.value + "'",

def show_nodes(node, tabs):
	for x in node.childNodes:
		for tab in range(0, tabs):
			print "    ",

		if x.localName != None:
			print "<" + x.localName,
			show_attributes(x.attributes)
			print " />"

		show_nodes(x, tabs+1)
