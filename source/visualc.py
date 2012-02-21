import project_object
import os
import project_path

class VisualC():
	def __init__(self, project, source_root, platform):
		self.source_project = project

	def write(self, creator, name):
		output = creator.create_file(name + ".vcxproj")
		self.project = Project(self.source_project, output.target_path)
		self.document = Document(self.project)
		self.document.write(output)
		self.document.close(output)
		output.close()

class ClInclude(project_object.WriterObject):
	def __init__(self, relative_file_path):
		self.Include = relative_file_path

class ClCompile(project_object.WriterObject):
	def __init__(self, relative_file_path):
		self.Include = relative_file_path

class CompileAs(project_object.WriterObject):
	def __init__(self, compile_as):
		self.Include = relative_file_path
		
		
class ClCompileDefinition(project_object.WriterObject):
	def __init__(self, attribs):
		project_object.WriterObject.__init__(self)
		self.attribs = attribs

	def name(self):
		return "ClCompile"

class Document(project_object.WriterObject):
	def __init__(self, projects):
		self.Project = projects

	def write(self, output):
		output.output('<?xml version="1.0" encoding="utf-8"?>')
		project_object.WriterObject.write(self.Project, output)

	def close(self, output):
		project_object.WriterObject.close(self.Project, output)

class Import(project_object.WriterObject):
	pass

class ItemDefinitionGroup(project_object.WriterObject):
	def __init__(self, condition, compile_options, link_options):
		self.Condition = condition
		self.compile = [ClCompileDefinition(compile_options), ]
		self.link = [Link(link_options), ]

class ItemGroup(project_object.WriterObject):
	pass

class ImportGroup(project_object.WriterObject):
	def __init__(self, label):
		self.Label = label

class Link(project_object.WriterObject):
	def __init__(self, options):
		self.attribs = options

class ProjectConfiguration(project_object.WriterObject):
	def __init__(self, include_configuration):
		self.Include = include_configuration

class PropertyGroup(project_object.WriterObject):
	pass

class Project(project_object.WriterObject):
	def __init__(self, project, write_path):
		self.DefaultTargets = "Build"
		self.ToolsVersion = "4.0"
		self.target_path = ""
		self.xmlns = "http://schemas.microsoft.com/developer/msbuild/2003"

		project_configurations_item_group = ItemGroup()
		project_configurations_item_group.Label = "ProjectConfigurations"

		debug_configuration = ProjectConfiguration("Debug|Win32")
		debug_configuration.attribs = {"Configuration": "Debug", "Platform": "Win32" }

		release_configuration = ProjectConfiguration("Release|Win32")
		release_configuration.attribs = {"Configuration": "Release", "Platform": "Win32" }

		project_configurations_item_group.configurations = [debug_configuration, release_configuration]

		source_files = project.settings.root_source_files.source_filenames()

		files_to_compile_item_group = ItemGroup()
		files_to_compile_item_group.files = []

		files_to_include_item_group = ItemGroup()
		files_to_include_item_group.files = []

		for filename in source_files:
			extension = os.path.splitext(filename)[1][1:]
			relative_filename = project_path.Path(filename).relative(write_path)
			if extension == "h" or extension == "hpp" or extension == "inc":
				files_to_include_item_group.files.append(ClInclude(relative_filename))
			elif extension == "cpp":
				files_to_compile_item_group.files.append(ClCompile(relative_filename))
			elif extension == "c":
				c = ClCompile(relative_filename)
				c.other = {"CompileAs": "CompileAsCpp" }
				files_to_compile_item_group.files.append(c)

		globals_property_group = PropertyGroup()
		globals_property_group.Label = "Globals"
		globals_property_group.attribs = {"ProjectGuid": "{95F04BB7-67C7-4BD5-9BF4-79E24D45023E}", "Keyword": "Win32Proj", "RootNamespace": "mergeblob"}

		default_props_import = Import()
		default_props_import.Project = "$(VCTargetsPath)\Microsoft.Cpp.Default.props"

		debug_configuration_property_group = PropertyGroup()
		debug_configuration_property_group.Condition = "'$(Configuration)|$(Platform)'=='Debug|Win32'"
		debug_configuration_property_group.Label = "Configuration"
		debug_configuration_property_group.attribs = {"ConfigurationType": "Application", "UseDebugLibraries": "true", "PlatformToolset": "v110", "CharacterSet": "NotSet"}

		release_configuration_property_group = PropertyGroup()
		release_configuration_property_group.Condition = "'$(Configuration)|$(Platform)'=='Release|Win32'"
		release_configuration_property_group.Label = "Configuration"
		release_configuration_property_group.attribs = {"ConfigurationType": "Application", "UseDebugLibraries": "false",  "PlatformToolset": "v110", "CharacterSet": "NotSet"}

		self.item_groups = [project_configurations_item_group, files_to_compile_item_group, files_to_include_item_group, globals_property_group, default_props_import, debug_configuration_property_group, release_configuration_property_group]

		user_props_import = Import()
		user_props_import.Project ="$(UserRootDir)\Microsoft.Cpp.$(Platform).user.props"
		user_props_import.Condition="exists('$(UserRootDir)\Microsoft.Cpp.$(Platform).user.props')"
		user_props_import.Label="LocalAppDataPlatform"

		extension_settings_import_group = ImportGroup("ExtensionSettings")
		props_import = Import()
		props_import.Project="$(VCTargetsPath)\Microsoft.Cpp.props"
		debug_property_sheets = ImportGroup("PropertySheets")
		debug_property_sheets.Condition="'$(Configuration)|$(Platform)'=='Debug|Win32'"
		debug_property_sheets.imports= [user_props_import, ]

		release_property_sheets = ImportGroup("PropertySheets")
		release_property_sheets.Condition="'$(Configuration)|$(Platform)'=='Release|Win32'"
		release_property_sheets.imports= [user_props_import, ]


		user_macros_property_group = PropertyGroup()
		user_macros_property_group.Label="UserMacros"

		debug_link_property_group = PropertyGroup()
		debug_link_property_group.Condition ="'$(Configuration)|$(Platform)'=='Debug|Win32'"
		debug_link_property_group.attribs = {"LinkIncremental": "true"}


		release_link_property_group = PropertyGroup()
		release_link_property_group.Condition ="'$(Configuration)|$(Platform)'=='Release|Win32'"
		release_link_property_group.attribs = {"LinkIncremental": "false"}

		include_paths = []
		for header_path in project.settings.include_paths():
			header_path = project_path.Path(header_path).relative(write_path)
			include_paths.append(header_path)

		include_paths = ";".join(include_paths)
		
		additionalIncludeDirectories = include_paths + ";%(AdditionalIncludeDirectories)"

		library_paths = []
		for library_filename in project.settings.library_filenames:
			library_paths.append(library_filename)

		library_path_string = ";".join(library_paths)
		additionalDependencies = library_path_string + ";%(AdditionalDependencies)"
		project_specific_defines_string = ";".join(project.settings.defines)
	
		debug_defines = ";".join(project.settings.defines + project.configurations["debug"].defines + ["WIN32", "_DEBUG", "_CONSOLE", "%(PreprocessorDefinitions)"])
		release_defines = ";".join(project.settings.defines + project.configurations["release"].defines + ["WIN32", "NDEBUG", "_CONSOLE", "%(PreprocessorDefinitions)"])
                                           
		library_dir = ";".join(project.settings.library_search_paths)
										   
		debug_compile_options = {"PrecompiledHeader": "", "WarningLevel": "Level4", "Optimization": "Disabled", "FunctionLevelLinking": "true", "IntrinsicFunctions": "true", "PreprocessorDefinitions": debug_defines, "AdditionalIncludeDirectories": additionalIncludeDirectories}
		debug_link_options = {"SubSystem": "Console", "GenerateDebugInformation": "true", "AdditionalDependencies": additionalDependencies, "AdditionalLibraryDirectories": library_dir + ";%(AdditionalLibraryDirectories)" }
		debug_compile_item_definition_group = ItemDefinitionGroup("'$(Configuration)|$(Platform)'=='Debug|Win32'", debug_compile_options, debug_link_options)

		release_compile_options = {"PrecompiledHeader": "", "WarningLevel": "Level4", "Optimization": "MaxSpeed", "FunctionLevelLinking": "true", "IntrinsicFunctions": "true", "PreprocessorDefinitions": release_defines, "AdditionalIncludeDirectories": additionalIncludeDirectories}
		release_link_options = {"SubSystem": "Console", "GenerateDebugInformation": "true", "EnableCOMDATFolding":"true", "OptimizeReferences": "true", "AdditionalDependencies": additionalDependencies, "AdditionalLibraryDirectories": library_dir + ";%(AdditionalLibraryDirectories)"}
		release_compile_item_definition_group = ItemDefinitionGroup("'$(Configuration)|$(Platform)'=='Release|Win32'", release_compile_options, release_link_options)

		import_targets = Import()
		import_targets.Project = "$(VCTargetsPath)\Microsoft.Cpp.targets"
		extension_targets_import_group = ImportGroup("ExtensionTargets")

		self.item_groups2 = [extension_targets_import_group, props_import, extension_settings_import_group,  debug_property_sheets, release_property_sheets, user_macros_property_group, debug_link_property_group, release_link_property_group, debug_compile_item_definition_group, release_compile_item_definition_group, import_targets, extension_targets_import_group]
