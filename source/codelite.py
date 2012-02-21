import project_writer
import os
import project_path
import re

class CodeLiteNode(object):
	def __init__(self):
		self.children = []
	
class Settings(CodeLiteNode):
	def __init__(self):
		super(Settings, self).__init__()
		self.Type = "Executable"

class GlobalSettings(CodeLiteNode):
	def __init__(self):
		super(GlobalSettings, self).__init__()

class Compiler(CodeLiteNode):
	def __init__(self):
		super(Compiler, self).__init__()
		self.Options = ""
		self.C_Options = ""
		self.Required = "yes"
		self.PreCompiledHeader = ""
		pass

class IncludePath(CodeLiteNode):
	def __init__(self, path):
		super(IncludePath, self).__init__()
		self.Value = path
		pass

class Linker(CodeLiteNode):
	def __init__(self):
		super(Linker, self).__init__()
		self.Options = ""
		pass

class LibraryPath(CodeLiteNode):
	def __init__(self, path):
		super(LibraryPath, self).__init__()
		self.Value = path

class Library(CodeLiteNode):
	def __init__(self, filename):
		super(Library, self).__init__()
		self.Value = filename

class Configuration(CodeLiteNode):
	def __init__(self, name):
		super(Configuration, self).__init__()
		self.Name = name
		self.CompilerType = "gnu g++"
		self.DebuggerType = "GNU gdb debugger"
		self.Type = ""
		self.BuildCmpWithGlobalSettings = "append"
		self.BuildLnkWithGlobalSettings = "append"
		self.BuildResWithGlobalSettings = "append"

class General(CodeLiteNode):
	def __init__(self, configuration_name):
		super(General, self).__init__()
		self.OutputFile = "$(IntermediateDirectory)/$(ProjectName)"
		self.IntermediatedDirectory = "./" + configuration_name
		self.Command = "./$(ProjectName)"
		self.CommandArguments = ""
		self.WorkingDirectory = "$(IntermediateDirectory)"
		self.PauseExecWhenProcTerminates = "yes"

class VirtualDirectory(CodeLiteNode):
	def __init__(self, name):
		super(VirtualDirectory, self).__init__()
		self.Name = name

class File(CodeLiteNode):
	def __init__(self, name):
		super(File, self).__init__()
		self.Name = name
		pass

class Project(CodeLiteNode):
	def __init__(self, project_name, config_name, inside_config):
		super(Project, self).__init__()
		self.Name = project_name
		if inside_config:
			self.ConfigName = config_name
		else:
			self.Path = project_name + ".project"
			self.Active = "Yes"

class WorkspaceConfiguration(CodeLiteNode):
	def __init__(self, project_name, name, selected):
		super(WorkspaceConfiguration, self).__init__()
		self.Name = name
		self.Selected = "yes" if selected else "no"
		project = Project(project_name, name, True)
		self.children.append(project)

class BuildMatrix(CodeLiteNode):
	def __init__(self, project):
		super(BuildMatrix, self).__init__()
		first_config = True
		print("CONFIGS:" + str(project.configurations))
		for name in project.configurations.keys():
			config = project.configurations[name]
			workspace_config = WorkspaceConfiguration(project.name(), config.name, first_config)
			self.children.append(workspace_config)
			first_config = False

class CodeLite_Workspace(CodeLiteNode):
	def __init__(self, project):
		super(CodeLite_Workspace, self).__init__()
		self.Name = project.name()
		self.Database = "./" + self.Name + ".tags"

		codelite_project = Project(project.name(), "", False)
		self.children.append(codelite_project)

		build_matrix = BuildMatrix(project)
		self.children.append(build_matrix)

class CodeLite_Project(CodeLiteNode):
	def __init__(self, project):
		super(CodeLite_Project, self).__init__()
		self.Name = project.name()
		self.InternalType = "Console"
		self.generate(project)

	def generate(self, project_definition):
		settings = self.add_global_settings(self.children, project_definition.settings)
		self.common_compiler_options = "-Wall"
		for name in project_definition.configurations.keys():
			config = project_definition.configurations[name]
			if name == "debug":
				options_to_add = "-g"
			else:
				options_to_add = ""
			self.add_configuration(settings.children, config, config.name, config.name, options_to_add)
		self.add_files(self.children, project_definition)

	def add_global_settings(self, parent, project):
		settings = Settings()
		parent.append(settings)

		global_settings = GlobalSettings()
		settings.children.append(global_settings)
		define_options_string = ""

		for define in project.defines:
			define_options_string += " -D" + define

		compiler = Compiler()
		global_settings.children.append(compiler)
		compiler.Options = define_options_string
		compiler.C_Options = define_options_string + " -std=c99"

		for include_path in project.include_paths():
			include_path_object = IncludePath(include_path)
			compiler.children.append(include_path_object)
		
		linker = Linker()
		global_settings.children.append(linker)

		for library_file_name in project.library_search_paths:
			library_path = LibraryPath(library_file_name)
			linker.children.append(library_path)

		for library_file_name in project.library_filenames:
			library_file = Library(library_file_name)
			linker.children.append(library_file)

		return settings

	def add_configuration(self, parent, settings, configuration_name, readable_name, options_to_add):
		config = Configuration(readable_name)
		
		compiler = Compiler()
		config.children.append(compiler)

		defines = settings.defines
		define_configuration_string = ""
		for define in defines:
			define_configuration_string += " -D" + define

		compiler.Options = self.common_compiler_options + " " + define_configuration_string + " " + options_to_add
		compiler.C_Options = self.common_compiler_options + " " + define_configuration_string + " " + options_to_add

		linker = Linker()
		config.children.append(linker)
		
		general = General(configuration_name)
		config.children.append(general)
		parent.append(config)
		
	def add_files(self, parent, project):
		vdir = VirtualDirectory("Code")
		parent.append(vdir)
		for filename in project.settings.source_filenames():
			f = File(filename)
			vdir.children.append(f)

class CodeLite:
	def __init__(self, project, source_root, platform):
		self.output = None
		self.project = project
		self.source_root = source_root
		self.generate_tree(project)

	def generate_tree(self, project):
		self.root = CodeLite_Project(project)
		self.workspace = CodeLite_Workspace(project)

	def output_name_value(self, name, value):
		return " " + name + "=\"" + value + "\""

	def output_scope_start(self, node):
		s = "<" + node.__class__.__name__
		
		for name in sorted(iter(node.__dict__.keys())):
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
		if isinstance(node, CodeLiteNode):
			self.output_scope_start(node)

	def output_node_children(self, children):
		for child in children:
			# exclude_properties = exclude_object.__dict__.keys()

			#if name in exclude_properties:
			#	continue

			self.output_value(child)

	def write(self, creator, name):
		self.output = creator.create_file(name + ".project")
		self.output.output('<?xml version="1.0" encoding="utf-8"?>')
		self.output_value(self.root)
		self.output.close()

		self.output = creator.create_file(name + ".workspace")
		self.output.output('<?xml version="1.0" encoding="utf-8"?>')
		self.output_value(self.workspace)
		self.output.close()

	def change_short_name_for_file_references(self, output):
		pass
