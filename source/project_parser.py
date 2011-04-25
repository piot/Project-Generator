import project_path

class Target:
	def __init__(self):
		self.name = ""
		self.type = ""

class Source:
	def __init__(self):
		self.directory = ""
		self.recursive = False
		self.exclude = ""
		self.compile_as_c = False

class Resource:
	def __init__(self):
		self.directory = ""
		self.recursive = False
		self.exclude = ""


class Platform:
	def __init__(self):
		self.name = ""

class Header:
	def __init__(self):
		self.directory = ""

class Library:
	def __init__(self):
		self.filename = ""

class LibraryPath:
	def __init__(self):
		self.directory = ""

class Dependency:
	def __init__(self):
		self.filename = ""
		self.merge = False
		
class Definer:
	def __init__(self):
		self.name = ""

class Parser:

	def parse(self, node, project, root_directory, platform_string):
		self.project = project
		self.root_directory = root_directory
		self.platform_string = platform_string


		for sub_node in node.childNodes:
			if sub_node.localName == "target":
				target = Target()
				self.parse_object(target, sub_node)
				self.project.set_name(target.name)
				data_dir = root_directory
#				plist_filename = data_dir + project.name() + ".plist"
#				import os
#				if not os.path.exists(plist_filename):
#					import project_writer
#					plist_output = project_writer.ProjectFileOutput(plist_filename)
#					import xcode_properties
#					xcode_properties.PropertyListWriter(plist_output, project.name())

				self.project.set_target_type(target.type)
				self.parse_target_sub_nodes(sub_node)

	def parse_target_sub_nodes(self, node):
		for sub_node in node.childNodes:
			if sub_node.localName == "source":
				source = Source()
				self.parse_object(source, sub_node)
				self.project.add_source_directory(source.directory, source.recursive, source.exclude)
#			if sub_node.localName == "resource":
#				resource = Resource()
#				self.parse_object(resource, sub_node)
#				self.project.add_resource_directory(resource.directory, resource.recursive, resource.exclude)
			elif sub_node.localName == "dependency":
				dependency = Dependency()
				self.parse_object(dependency, sub_node)
				self.project.add_dependency(dependency.filename, dependency.merge)
			elif sub_node.localName == "header":
				header = Header()
				self.parse_object(header, sub_node)
				directory = header.directory.replace("\\", "/")
				self.project.add_header_directory(directory)
			elif sub_node.localName == "library":
				library = Library()
				self.parse_object(library, sub_node)
				self.project.add_library_filename(library.filename)

			elif sub_node.localName == "library-path":
				library_path = LibraryPath()
				self.parse_object(library_path, sub_node)
				self.project.add_library_search_path(library_path.directory)

			elif sub_node.localName == "platform":
				platform = Platform()
				self.parse_object(platform, sub_node)
				if platform.name == self.platform_string:
					self.parse_target_sub_nodes(sub_node)
			elif sub_node.localName == "define":
				d = Definer()
				self.parse_object(d, sub_node)
				self.project.add_define(d.name)

	def convert_path(self, path):
		new_path = project_path.Path(self.root_directory).join(path)
		new_path = new_path.replace("\\", "/")
		return new_path

	def parse_object(self, o, node):
		attributes = node.attributes
		for i in range(attributes.length):
			item = attributes.item(i)
			if "directory" in item.name:
				before = item.value
				item.value = self.convert_path(item.value)
			elif item.value != "" and item.value[0] == "[":
				value = item.value[1:-1]
				value_list = value.split()
				value = "".join(value_list)
				item.value = value.split(",")
			setattr(o, item.name, item.value)

