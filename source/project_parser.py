import project_path
import os

class Target:
	def __init__(self):
		self.name = ""
		self.type = ""

class Source:
	def __init__(self):
		self.directory = ""
		self.recursive = False
		self.exclude = ""
		self.compile_as = ""

class Resource:
	def __init__(self):
		self.directory = ""
		self.recursive = False
		self.exclude = ""

class Platform:
	def __init__(self):
		self.name = ""

class Configuration:
	def __init__(self):
		self.name = ""
		self.define = ""

class Header:
	def __init__(self):
		self.directory = ""

class Library:
	def __init__(self):
		self.filename = ""

class LibraryPath:
	def __init__(self):
		self.directory = ""

class FrameworkPath:
	def __init__(self):
		self.directory = ""

class Compiler:
	def __init__(self):
		self.flags = ""
		self.compiler = ""

class Linker:
	def __init__(self):
		self.flags = ""
		self.linker = ""

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

				self.project.set_target_type(target.type)
				self.parse_target_sub_nodes(sub_node, self.project.settings)

	def parse_target_sub_nodes(self, node, settings):
		for sub_node in node.childNodes:
			if sub_node.localName == "source":
				source = Source()
				self.parse_object(source, sub_node)
				settings.add_source_directory(source.directory, source.recursive, source.exclude)

			elif sub_node.localName == "dependency":
				dependency = Dependency()
				self.parse_object(dependency, sub_node)
				self.project.add_dependency(dependency.filename, dependency.merge)

			elif sub_node.localName == "header":
				header = Header()
				self.parse_object(header, sub_node)
				directory = header.directory.replace("\\", "/")
				settings.add_header_directory(directory)

			elif sub_node.localName == "library":
				library = Library()
				self.parse_object(library, sub_node)
				settings.add_library_filename(library.filename)
				extension = os.path.splitext(library.filename)[1][1:]
				if extension == "framework":
					if library.filename[0:3] == "../":
						library.filename = self.convert_path(library.filename)
						directory = os.path.dirname(library.filename[0:-1])
						settings.add_framework_search_path(directory)


			elif sub_node.localName == "library-path":
				library_path = LibraryPath()
				self.parse_object(library_path, sub_node)
				settings.add_library_search_path(library_path.directory)

			elif sub_node.localName == "compiler":
				compiler = Compiler()
				self.parse_object(compiler, sub_node)
				settings.set_compiler(compiler.program, compiler.flags)

			elif sub_node.localName == "linker":
				linker = Linker()
				self.parse_object(linker, sub_node)
				print("LINKER: ", linker.program, linker.flags)
				settings.set_linker(linker.program, linker.flags)

			elif sub_node.localName == "platform":
				platform = Platform()
				self.parse_object(platform, sub_node)
				if platform.name == self.platform_string:
					# print("We should parse platform:", self.platform_string)
					self.parse_target_sub_nodes(sub_node, settings)
					#print("********** platform:", self.platform_string)

			elif sub_node.localName == "define":
				d = Definer()
				self.parse_object(d, sub_node)
				settings.add_define(d.name)

			elif sub_node.localName == "configuration":
				c = Configuration()
				self.parse_object(c, sub_node)
				sub_config = self.project.configuration(c.name)
				self.parse_target_sub_nodes(sub_node, sub_config)

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
