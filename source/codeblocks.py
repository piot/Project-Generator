import project_writer
import os
import project_path
import re

class CodeBlocksNode(object):
	def __init__(self):
		self.children = []
	
class CodeBlocks_project_file(CodeBlocksNode):
	def __init__(self):
		super(CodeBlocks_project_file, self).__init__()

class FileVersion(CodeBlocksNode):
	def __init__(self, major, minor):
		super(FileVersion, self).__init__()
		self.major = major
		self.minor = minor

class Target(CodeBlocksNode):
	def __init__(self, title):
		super(Target, self).__init__()
		self.title = title

class Compiler(CodeBlocksNode):
	def __init__(self):
		super(Compiler, self).__init__()
		pass

class Linker(CodeBlocksNode):
	def __init__(self):
		super(Linker, self).__init__()
		pass

class Option(CodeBlocksNode):
	def __init__(self):
		super(Option, self).__init__()
		pass

class Unit(CodeBlocksNode):
	def __init__(self):
		super(Unit, self).__init__()

class Extensions(CodeBlocksNode):
	def __init__(self):
		super(Extensions, self).__init__()


class code_completion(CodeBlocksNode):
	def __init__(self):
		super(code_completion, self).__init__()

class debugger(CodeBlocksNode):
	def __init__(self):
		super(debugger, self).__init__()

class Add(CodeBlocksNode):
	def __init__(self):
		super(Add, self).__init__()
		pass

class Build(CodeBlocksNode):
	def __init__(self):
		super(Build, self).__init__()

class Project(CodeBlocksNode):
	def __init__(self, project):
		super(Project, self).__init__()
		self.generate(project)

	def add_output_path(self, parent, configuration_name, project_name):
		output = Option()
		output.output = "bin/" + configuration_name + "/" + project_name
		output.prefix_auto = "1"
		output.extension_auto = "1"
		parent.append(output)

	def add_object_output_path(self, parent, configuration_name):
		object_output = Option()
		object_output.object_output = "obj/" + configuration_name
		parent.append(object_output)

	def add_target(self, parent, project, configuration_name, formal_configuration_name):
		target = Target(configuration_name)
		self.add_output_path(target.children, configuration_name, project.name())
		self.add_object_output_path(target.children, configuration_name)
		target_type = Option()
		target_type.type = "1"
		compiler = Compiler()
		target.children.append(compiler)
		parent.append(target)

		defines = project.configurations[formal_configuration_name].defines
		for define in defines:
			add_define = Add()
			add_define.option = "-D" + define
			compiler.children.append(add_define)

		return target, compiler
		
	def add_debug_target(self, parent, project):
		target, compiler = self.add_target(parent, project, "Debug", "debug")
		add = Add()
		add.option = "-g"
		compiler.children.append(add)
	
	def add_release_target(self, parent, project):
		target, compiler = self.add_target(parent, project, "Release", "release")
		add = Add()
		add.option = "-O2"
		compiler.children.append(add)
		linker = Linker()
		add = Add()
		add.option = "-s"
		linker.children.append(add)
		target.children.append(linker)

	def add_build(self, parent, project):
		build = Build()
		self.add_debug_target(build.children, project)
		self.add_release_target(build.children, project)
		parent.append(build)

	def add_global_compiler_options(self, parent, project):
		compiler = Compiler()
		add = Add()
		add.option = "-Wall"
		compiler.children.append(add)

		for include_path in project.settings.include_paths():
			add = Add()
			add.directory = include_path
			compiler.children.append(add)

		for define in project.settings.defines:
			add_define = Add()
			add_define.option = "-D" + define
			compiler.children.append(add_define)			

		parent.append(compiler)

	def add_global_linker_options(self, parent, project):
		linker = Linker()
		for library_file_name in project.settings.library_filenames:
			add = Add()
			add.library = library_file_name
			linker.children.append(add)

		parent.append(linker)
		
	def add_units(self, parent, project):
		for filename in project.settings.source_filenames():
			unit = Unit()
			unit.filename = filename
			parent.append(unit)

	def add_extensions(self, parent):
		extensions = Extensions()
		extensions.children.append(code_completion())
		extensions.children.append(debugger())
		parent.append(extensions)

	def add_global_project_options(self, parent):
		title = Option()
		title.title = "Tyran"
		parent.append(title)

		pch = Option()
		pch.pchmode = "2"
		parent.append(pch)

		compiler = Option()
		compiler.compiler = "gcc"
		parent.append(compiler)

	def generate(self, project_definition):
		self.add_global_project_options(self.children)
		self.add_build(self.children, project_definition)
		self.add_global_compiler_options(self.children, project_definition)
		self.add_global_linker_options(self.children, project_definition)
		self.add_units(self.children, project_definition)
		self.add_extensions(self.children)

class CodeBlocks:
	def __init__(self, project, source_root, platform):
		self.output = None
		self.project = project
		self.source_root = source_root
		self.generate_tree()

	def generate_tree(self):
		self.root = CodeBlocks_project_file()
		major = "1"
		minor = "6"
		self.root.children.append(FileVersion(major, minor))
		self.root.children.append(Project(self.project))

	def output_name_value(self, name, value):
		return " " + name + "=\"" + value + "\""

	def output_scope_start(self, node):
		s = "<" + node.__class__.__name__
		
		for name in sorted(iter(node.__dict__)):
			if name == "children":
				continue
			value = node.__dict__[name]
			s = s + self.output_name_value(name, value)

		if len(node.children) > 0:
			s = s + ">"
			self.output.output(s);
			self.output.increase_tabs()
			self.output_node_children(node.children)
			self.output.decrease_tabs()
			self.output_scope_end(node)
		else:
			s = s + "/>"
			self.output.output(s);
		
	def output_scope_end(self, node):
		self.output.output("</" + node.__class__.__name__ + ">")
		
	def output_value(self, node):
		if isinstance(node, CodeBlocksNode):
			self.output_scope_start(node)

	def output_node_children(self, children):
		for child in children:
			# exclude_properties = exclude_object.__dict__.keys()

			#if name in exclude_properties:
			#	continue

			self.output_value(child)

	def write(self, creator, name):
		self.output = creator.create_file(name + ".project")
		self.output.output('<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>')
		self.output_value(self.root)
		self.output.close()

	def close(self, output):
		pass

	def change_short_name_for_file_references(self, output):
		pass
