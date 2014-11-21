import project_writer
import os
import project_path
import re

class XcodeId():
	def __init__(self, id_string):
		self.id_string = id_string
		assert(len(self.id_string) == 24)

	def __str__(self):
		return self.id_string;

class XcodeIdHolder():
	def __init__(self):
		self.id = 0

	def generate_id(self):
		self.id += 1
		id_string = "%024X" % self.id
		id = XcodeId(id_string)
		return id

class XcodeObjectCreator():
	def __init__(self):
		self.id_holder = XcodeIdHolder()

	def create(self, cls, *args):
		xcode_id = self.id_holder.generate_id()
		new_object = cls(xcode_id, *args)
		return new_object

class XcodeWriterScope(project_writer.ProjectWriter):
	def __init__(self, keyword):
		project_writer.ProjectWriter.__init__(self)
		self.keyword = keyword

	def write(self, output):
		output.output(str(self.keyword) + " = {")
		output.increase_tabs()

	def close(self, output):
		project_writer.ProjectWriter.close(self, output)
		output.decrease_tabs()
		output.output( "};" )

class XcodeWriterLine(project_writer.ProjectWriter):
	def __init__(self, keyword, value):
		project_writer.ProjectWriter.__init__(self)
		self.keyword = keyword
		self.value = value

	def write(self, output):
		value = add_quotation_marks_when_needed(self.value)
		keyword = add_quotation_marks_when_needed(self.keyword)
		output.output(keyword + " = " + value + ";" )

class XcodeWriterCollection(project_writer.ProjectWriter):
	def __init__(self, keyword, ids):
		project_writer.ProjectWriter.__init__(self)
		self.keyword = keyword
		self.ids = ids

	def write(self, output):
		s = self.keyword + " = ("
		output.output(s)
		output.increase_tabs()
		for id_object in self.ids:
			output.output( add_quotation_marks_when_needed(id_object) + ",")

	def close(self, output):
		output.decrease_tabs()
		output.output( ");")

class XcodeWriterDictionary(XcodeWriterScope):
	def __init__(self, keyword, dictionary):
		XcodeWriterScope.__init__(self, keyword)
		self.dictionary = dictionary

	def write(self, output):
		XcodeWriterScope.write(self, output)
		for name in sorted(self.dictionary.iterkeys()):
			value = self.dictionary[name]
			output_value(name, value, output)

class XcodeProjectSectionObjectWriter(XcodeWriterScope):
	def __init__(self, keyword, section_object):
		XcodeWriterScope.__init__(self, keyword)
		self.section_object = section_object

	def write(self, output):
		XcodeWriterScope.write(self, output)
		self.section_object.write(output)

	def close(self, output):
		self.section_object.close(output)
		XcodeWriterScope.close(self, output)

class XcodeWriterDocument(project_writer.ProjectWriter):
	def write(self, output):
		project_writer.ProjectWriter.write(self, output)
		output.output("// !$*UTF8*$!\n{");
		output.increase_tabs();

	def close(self, output):
		project_writer.ProjectWriter.close(self, output)
		output.decrease_tabs();
		output.output("}");

class XcodeReference(project_writer.ProjectWriter):
	def __init__(self, xcode_id, comment):
		project_writer.ProjectWriter.__init__(self)

		self.xcode_id = xcode_id
		self.comment = comment

	def __str__(self):
		return str(self.xcode_id) + " /* " + self.comment + " */ ";

def output_value(name, value, output):
	if isinstance(value, list):
		write_object = XcodeWriterCollection(name, value)
	elif isinstance(value, dict):
		write_object = XcodeWriterDictionary(name, value)
	elif isinstance(value, XcodeProjectSectionObject):
		write_object = XcodeProjectSectionObjectWriter(name, value)
	else:
		write_object = XcodeWriterLine(name, value)

	write_object.write(output)
	write_object.close(output)

def add_quotation_marks_when_needed(value):
	if isinstance(value, XcodeReference):
		return str(value)



	value = str(value)
	all_characters_are_representable = re.match('[a-zA-Z./_0-9]*', value)
	if value == "" or (not all_characters_are_representable) or all_characters_are_representable.group(0) != value:
		value = '"' + value + '"'
	return value

class XcodeProjectObjectRaw(XcodeReference):
	def write_all_attributes(self, output, exclude_object = None):
		if not exclude_object:
			exclude_object = XcodeProjectObject(None, None)

		for name in sorted(self.__dict__.iterkeys()):
			exclude_properties = exclude_object.__dict__.keys()

			if name in exclude_properties:
				continue

			value = self.__dict__[name]
			output_value(name, value, output)

	def write(self, output):
		self.write_all_attributes(output)

class XcodeProjectObject(XcodeProjectObjectRaw):
	def __init__(self, xcode_id, comment):
		XcodeProjectObjectRaw.__init__(self, xcode_id, comment)

	def write(self, output):
		self.push(XcodeWriterScope(self), output)
		XcodeWriterLine("isa", self.__class__.__name__).write(output)
		self.write_all_attributes(output)

class PBXBuildFile(XcodeProjectObject):
	def __init__(self, xcode_id, file_ref):
		self.fileRef = file_ref
		comment = os.path.basename(file_ref.path)

		XcodeProjectObject.__init__(self, xcode_id, comment)

	def change_target_path(self, target_path):
		pass

class BuildPhase(XcodeProjectObject):
	def __init__(self, xcode_id, comment, file_references):
		self.files = file_references
		self.buildActionMask = 2147483647

		self.runOnlyForDeploymentPostprocessing = 0
		XcodeProjectObject.__init__(self, xcode_id, comment)

class PBXFrameworksBuildPhase(BuildPhase):
	def __init__(self, xcode_id, file_references):
		comment = "Frameworks build phase"
		BuildPhase.__init__(self, xcode_id, comment, file_references)

class PBXHeadersBuildPhase(BuildPhase):
	def __init__(self, xcode_id, file_references):
		comment = "Headers build phase"
		BuildPhase.__init__(self, xcode_id, comment, file_references)

class PBXSourcesBuildPhase(BuildPhase):
	def __init__(self, xcode_id, file_references):
		comment = "Sources build phase"
		BuildPhase.__init__(self, xcode_id, comment, file_references)

class PBXResourcesBuildPhase(BuildPhase):
	def __init__(self, xcode_id, file_references):
		comment = "Resources build phase"
		BuildPhase.__init__(self, xcode_id, comment, file_references)

class PBXGroup(XcodeProjectObject):
	def __init__(self, xcode_id, name, children):
		self.children = children
		self.name = name
			
		self.sourceTree = "<group>"
		comment = name
		XcodeProjectObject.__init__(self, xcode_id, comment)

	def append_child(self, child):
		self.children.append(child)

	def find(self, name):
		for group in self.children:
			if isinstance(group, PBXGroup):
				try:
					if group.name == name:
						return group
				except:
					pass
		return None

class FilePath:
	def __init__(self, file_reference):
		self.file_reference = file_reference

	def __str__(self):
		return self.file_reference.path

class FilePaths:
	def __init__(self, file_references):
		self.paths = []
		for file_reference in file_references:
			self.paths.append(FilePath(file_reference))

	def __str__(self):
		paths = []
		for path in self.paths:
			paths.append(str(path))

		return " ".join(paths)


class PBXFileReference(XcodeProjectObject):
	def __init__(self, xcode_id, path):
		extension = os.path.splitext(path)[1][1:]
		if extension != "app":
			self.fileEncoding = 4

		if extension == "cpp":
			self.lastKnownFileType = "sourcecode.cpp.cpp"
			self.sourceTree = "SOURCE_ROOT"
		elif extension == "c":
			self.lastKnownFileType = "sourcecode.c.c"
			self.sourceTree = "SOURCE_ROOT"
		elif extension == "h" or extension == "pch":
			self.lastKnownFileType = "sourcecode.c.h"
			self.sourceTree = "SOURCE_ROOT"
		elif extension == "a":
			self.explicitFileType = "archive.ar"
			self.sourceTree = "<group>"
		elif extension == "framework":
			self.lastKnownFileType = "wrapper.framework"
			if path[0:3] == "../":
				self.sourceTree = "<group>"
			else:
				self.sourceTree = "SDKROOT"
		elif extension == "dylib":
			self.lastKnownFileType = "wrapper.framework"
			self.sourceTree = "SDKROOT"
		elif extension == "plist":
			self.lastKnownFileType = "text.plist.xml"
			self.sourceTree = "<group>"
			self.plistStructureDefinitionIdentifier = "com.apple.xcode.plist.structure-definition.iphone.info-plist"
		elif extension == "ogg":
			self.lastKnownFileType = "audio"
			self.sourceTree = "SOURCE_ROOT"
		elif extension == "m":
			self.lastKnownFileType = "sourcecode.c.objc"
			self.sourceTree = "SOURCE_ROOT"
		elif extension == "mm":
			self.lastKnownFileType = "sourcecode.cpp.objcpp"
			self.sourceTree = "SOURCE_ROOT"
		elif extension == "xib":
			self.lastKnownFileType = "file.xib"
			self.sourceTree = "SOURCE_ROOT"
		elif extension == "storyboard":
			self.lastKnownFileType = "file.storyboard"
			self.sourceTree = "SOURCE_ROOT"
		elif extension == "oes":
			self.lastKnownFileType = "text"
			self.sourceTree = "SOURCE_ROOT"
		elif extension == "oec":
			self.lastKnownFileType = "text"
			self.sourceTree = "SOURCE_ROOT"
		elif extension == "oeb":
			self.lastKnownFileType = "text"
			self.sourceTree = "SOURCE_ROOT"
		elif extension == "png":
			self.lastKnownFileType = "image.png"
			self.sourceTree = "SOURCE_ROOT"
		elif extension == "icns":
			self.lastKnownFileType = "image.icns"
			self.sourceTree = "SOURCE_ROOT"
		elif extension == "app":
			self.explicitFileType = "wrapper.application"
			self.sourceTree = "BUILT_PRODUCTS_DIR"
			self.includeInIndex = 0
#		else:
#			raise Exception("Unknown extension:" + extension)

		self.path = path
		comment = os.path.basename(path)
		XcodeProjectObject.__init__(self, xcode_id, comment)

	def change_target_path(self, target_path):
		extension = os.path.splitext(self.path)[1][1:]
		if self.path[0:7] != "System/" and extension != "dylib" and extension != "app" and os.path.dirname(self.path) != "":
			relative_filename = project_path.Path(self.path).relative(target_path)
			self.path = relative_filename

class PBXNativeTarget(XcodeProjectObject):
	def __init__(self, xcode_id, name, product_file_reference, configuration_list, build_phases, product_type):
		self.buildConfigurationList = configuration_list
		self.buildPhases = build_phases
		self.buildRules = []
		self.dependencies = []
		self.name = name
		self.productName = name
		self.productReference = product_file_reference
		if product_type == "library":
			self.productType = "com.apple.product-type.library.static"
		else:
			self.productType = "com.apple.product-type.application"
		comment = name
		XcodeProjectObject.__init__(self, xcode_id, comment)

class PBXProject(XcodeProjectObject):
	def __init__(self, xcode_id, build_configuration_list, main_group, product_ref_group, target_list):
		self.buildConfigurationList = build_configuration_list
		self.compatibilityVersion = "Xcode 3.2";
		self.hasScannedForEncodings = 1;
		self.mainGroup = main_group
		self.productRefGroup = product_ref_group # Not present in Applications!?
		self.projectDirPath = ""
		self.projectRoot = ""
		self.targets = target_list
		comment = "Project"
		XcodeProjectObject.__init__(self, xcode_id, comment)

class XCBuildConfiguration(XcodeProjectObject):
	def __init__(self, xcode_id, name, build_settings, usage):
		self.buildSettings = build_settings
		self.name = name;
		comment = name + " build settings " + usage
		XcodeProjectObject.__init__(self, xcode_id, comment)

class XCConfigurationList(XcodeProjectObject):
	def __init__(self, xcode_id, build_configurations, default_configuration_name, usage):
		self.buildConfigurations = build_configurations
		self.defaultConfigurationIsVisible = 0
		self.defaultConfigurationName = default_configuration_name
		comment = "Build configuration list for " + usage
		XcodeProjectObject.__init__(self, xcode_id, comment)

class XcodeSection(project_writer.ProjectWriter):
	def __init__(self, section_name):
		project_writer.ProjectWriter.__init__(self)
		self.section_name = section_name

	def write(self, output):
		output.output("")
		output.output("/* Begin " + self.section_name + " section */")

	def close(self, output):
		output.output("/* End " + self.section_name + " section */")
		output.output("")
		project_writer.ProjectWriter.close(self, output)

class XcodeProjectSectionObject(project_writer.ProjectWriter):
	def write(self, output):
		project_writer.ProjectWriter.write(self, output)
		self.write_all_attributes(output)

	def write_all_attributes(self, output, exclude_object=project_writer.ProjectWriter()):
		section_infos = {}
		for name, value in self.__dict__.iteritems():
			exclude_properties = exclude_object.__dict__.keys()

			if name in exclude_properties:
				continue

			value = self.__dict__[name]
			if isinstance(value, list):
				section_name = value[0].__class__.__name__
			else:
				section_name = value.__class__.__name__

			if value == None:
				raise Exception("self." + name + " has illegal value!")
			section_infos[section_name] = value

		for section_name in sorted(section_infos.iterkeys()):
			value = section_infos[section_name]
			section = XcodeSection(section_name)
			section.write(output)
			if isinstance(value, list):
				for o in value:
					o.write(output)
					o.close(output)
			else:
				if not value:
					raise Exception("section:" + section_name + " in object:" + self.__class__.__name__)
				else:
					value.write(output)
					value.close(output)
			section.close(output)

def split_directories(path):
	directories = path.split("/")
	directories = directories[:-1]
	return directories

def create_directory_groups(object_factory, parent_group, source_root, absolute_filename):
	relative_filename = project_path.Path(absolute_filename).relative(source_root)
	
	absolute_directory = source_root
	
	directories = split_directories(relative_filename)
	for directory in directories:
		absolute_directory = os.path.normpath(os.path.join(absolute_directory, directory))
		if directory == ".." or directory == ".":
			continue

		child_group = parent_group.find(directory)
		if not child_group:
			child_group = object_factory.create(PBXGroup, directory, [])
			parent_group.append_child(child_group)
		parent_group = child_group
	return parent_group

class XcodeDefaultGroups:
	def __init__(self, creator, name):
		self.classes = creator.create(PBXGroup, "Classes", [])
		self.frameworks = creator.create(PBXGroup, "Frameworks", [])
		self.products = creator.create(PBXGroup, "Products", [])
		self.resources = creator.create(PBXGroup, "Resources", [])
		self.root = creator.create(PBXGroup, name, [self.classes, self.frameworks, self.products])

	def flatten_groups(self):
		groups = []
		self.add_group(groups, self.root)
		return groups

	def root_group(self):
		return self.root

	def add_group(self, groups, group):
		for child_group in group.children:
			if isinstance(child_group, PBXGroup):
				self.add_group(groups, child_group)

		groups.append(group)

class XcodeDefaultGroupsForApplication(XcodeDefaultGroups):
	def __init__(self, creator, name):
		XcodeDefaultGroups.__init__(self, creator, name)
		self.resources = creator.create(PBXGroup, "Resources", [])
		self.libraries = creator.create(PBXGroup, "Libraries", [])
		self.root.append_child(self.resources)
		self.root.append_child(self.libraries)

class XcodeObjects(XcodeProjectSectionObject):
	def __init__(self, project, source_root, platform):
		object_factory = XcodeObjectCreator()

		self.convert_library_names(project)

		if project.target_type == "library":
			default_groups = XcodeDefaultGroups(object_factory, project.name())
		else:
			default_groups = XcodeDefaultGroupsForApplication(object_factory, project.name())

		self.source_file_references = []
		self.build_files = []
		self.build_configurations = []
		self.configuration_lists = []

		extensions = ["cpp", "c", "h", "pch", "xib", "storyboard", "m", "mm"]
		self.generate_build_files(source_root, project.settings.source_filenames(), extensions, object_factory, default_groups.classes)
		extensions = ["plist"]
		self.generate_file_references(project.settings.source_filenames(), extensions, object_factory, default_groups.resources)
		extensions = None
		self.generate_build_files(source_root, project.settings.resource_filenames(), extensions, object_factory, default_groups.resources)

		if project.target_type == "library":
			project.library_filenames.append("Foundation.framework") # not sure if all libraries need Foundation?
			library_build_files = []
		else:
			library_build_files = self.create_build_files_for_extension(object_factory, source_root, default_groups.libraries, project.library_filenames, ["a"], "")

		framework_names = []
		for name in project.settings.framework_names:
			framework_names.append(name + ".framework")


			
		framework_build_files = self.create_build_files_for_extension(object_factory, source_root, default_groups.frameworks, framework_names, ["framework"], "System/Library/Frameworks/")
		
		dylib_build_files = self.create_build_files_for_extension(object_factory, source_root, default_groups.frameworks, project.library_filenames, ["dylib"], "System/Library/Frameworks/")

		all_framework_like_files = framework_build_files + dylib_build_files + library_build_files

		self.frameworks_build_phase = object_factory.create(PBXFrameworksBuildPhase, all_framework_like_files)
		source_build_files = self.all_source_build_files(project)
		self.sources_build_phase = object_factory.create(PBXSourcesBuildPhase, source_build_files)
		self.headers_build_phase = object_factory.create(PBXHeadersBuildPhase, self.all_header_build_files(project))
		self.resources_build_phase = object_factory.create(PBXResourcesBuildPhase, self.all_resource_build_files(project))

		self.groups = default_groups.flatten_groups()

		self.target_product = self.product(object_factory, default_groups.products, project.name(), project.target_type,  project.settings.library_search_paths, project.settings.framework_search_paths)
		if project.target_type == "library":
			header_paths = self.create_header_paths(object_factory, project.settings.header_paths)
			self.project = self.create_project_for_library(object_factory, project.name(), default_groups.root_group(), default_groups.products, self.target_product, header_paths, project.settings.defines,platform)
		else:

			header_paths = self.create_header_paths(object_factory, project.settings.header_paths)
			self.project = self.create_project_for_application(object_factory, project.name(), default_groups.root_group(), default_groups.products, self.target_product, header_paths, project.settings.defines, project.configurations, platform)

		XcodeProjectSectionObject.__init__(self)

	def create_header_paths(self, object_factory, header_paths):
		file_references = []
		for header_path in header_paths:
			file_reference = self.create_invisible_file_reference(object_factory, header_path)
			file_references.append(file_reference)

		return FilePaths(file_references)


	def convert_library_names(self, project):
		new_filenames = []
		for filename in project.settings.library_filenames:
			extension = os.path.splitext(filename)[1][1:]
			new_filenames.append(filename)

		project.library_filenames = new_filenames

	def create_build_files_for_extension(self, object_factory, source_root, root_group, filenames, extensions, path_prefix):
		build_files = []
		for filename in filenames:
			extension = os.path.splitext(filename)[1][1:]
			if extension in extensions:
				if extension == "framework" and filename[0:3] == "../":
					use_filename = filename
				else:
					use_filename = path_prefix + filename
				build_file = self.create_build_file(object_factory, source_root, use_filename, root_group)
				build_files.append(build_file)

		return build_files

	def change_target_path_for_file_references(self, target_path):
		for file_reference in self.source_file_references:
			file_reference.change_target_path(target_path)

		for file_reference in self.build_files:
			file_reference.change_target_path(target_path)

	def change_short_name_for_file_references(self, source_path):
		for file_reference in self.source_file_references:
			file_reference.change_short_name(source_path)

	def create_project_for_library(self, object_factory, name, root_group, products_group, target_product, header_paths, defines, platform):
		build_configuration_list = self.create_project_configuration_list_for_library(object_factory, name, header_paths, defines,platform)
		return object_factory.create(PBXProject, build_configuration_list, root_group, products_group, [target_product])

	def create_project_for_application(self, object_factory, name, root_group, products_group, target_product, header_paths, defines, configurations, platform):
		build_configuration_list = self.create_project_configuration_list_for_application(object_factory, name, header_paths, defines, configurations, platform)
		return object_factory.create(PBXProject, build_configuration_list, root_group, products_group, [target_product])

	def create_build_configuration(self, object_creator, name, build_settings, comment):
		configuration = object_creator.create(XCBuildConfiguration, name, build_settings, comment)
		self.build_configurations.append(configuration)
		return configuration

	def create_common_target_build_settings_for_application(self, name, plist_filename, library_search_paths, framework_search_paths):
		build_settings = {
			"ALWAYS_SEARCH_USER_PATHS": "NO",
			"GCC_PRECOMPILE_PREFIX_HEADER": "YES",
			"GCC_PREFIX_HEADER": name + "_Prefix.pch",
			"GCC_THUMB_SUPPORT": "NO",
			"USE_HEADERMAP": "NO",
			"INFOPLIST_FILE": plist_filename,
			"LIBRARY_SEARCH_PATHS": library_search_paths,
			# "FRAMEWORK_SEARCH_PATHS": framework_search_paths,
			"PRODUCT_NAME": name
		}
		return build_settings

	def create_target_debug_configuration_for_application(self, object_creator, name, plist_filename, library_search_paths, framework_search_paths):
		build_settings = self.create_common_target_build_settings_for_application(name, plist_filename, library_search_paths, framework_search_paths)
		build_settings["COPY_PHASE_STRIP"] = "NO"
		build_settings["GCC_DYNAMIC_NO_PIC"] = "NO"
		build_settings["GCC_OPTIMIZATION_LEVEL"] = 0
		return self.create_build_configuration(object_creator, "Debug", build_settings, "target")

	def create_target_release_configuration_for_application(self, object_creator, name, plist_filename, library_search_paths, framework_search_paths):
		build_settings = self.create_common_target_build_settings_for_application(name, plist_filename, library_search_paths, framework_search_paths)
		build_settings["COPY_PHASE_STRIP"] = "YES"
		return self.create_build_configuration(object_creator, "Release", build_settings, "target")

	def create_target_adhoc_configuration_for_application(self, object_creator, name, plist_filename, library_search_paths, framework_search_paths):
		build_settings = self.create_common_target_build_settings_for_application(name, plist_filename, library_search_paths, framework_search_paths)
		build_settings["COPY_PHASE_STRIP"] = "YES"
		return self.create_build_configuration(object_creator, "AdHoc", build_settings, "target")

	def create_target_distribution_configuration_for_application(self, object_creator, name, plist_filename, library_search_paths, framework_search_paths):
		build_settings = self.create_common_target_build_settings_for_application(name, plist_filename, library_search_paths, framework_search_paths)
		build_settings["COPY_PHASE_STRIP"] = "YES"
		return self.create_build_configuration(object_creator, "AppStore", build_settings, "target")

	def create_target_build_configurations_for_application(self, factory, name, plist_filename, library_search_paths, framework_search_paths):
		build_configurations = [
			self.create_target_debug_configuration_for_application(factory, name, plist_filename, library_search_paths, framework_search_paths),
			self.create_target_release_configuration_for_application(factory, name, plist_filename, library_search_paths, framework_search_paths),
			self.create_target_adhoc_configuration_for_application(factory, name, plist_filename, library_search_paths, framework_search_paths),
			self.create_target_distribution_configuration_for_application(factory, name, plist_filename, library_search_paths, framework_search_paths),
		]

		return build_configurations

	def create_common_target_build_settings_for_library(self, name):
		build_settings = {
			"ALWAYS_SEARCH_USER_PATHS": "NO",
			"ARCHS": "$(ARCHS_STANDARD_32_BIT)",
			"COPY_PHASE_STRIP": "NO",
			"DSTROOT": "/tmp/" + name  + ".dst",
			"GCC_MODEL_TUNING": "G5",
			"GCC_OPTIMIZATION_LEVEL": 0,
			"GCC_PRECOMPILE_PREFIX_HEADER": "YES",
			"GCC_PREFIX_HEADER": name + "_Prefix.pch",
			"INSTALL_PATH": "/usr/local/lib",
			"PRODUCT_NAME": name
		}
		return build_settings

	def create_target_debug_configuration_for_library(self, object_creator, name):
		build_settings = self.create_common_target_build_settings_for_library(name)
		build_settings.update( {
			"COPY_PHASE_STRIP": "NO",
			"GCC_DYNAMIC_NO_PIC": "NO",
			"GCC_ENABLE_FIX_AND_CONTINUE": "YES",
			"GCC_OPTIMIZATION_LEVEL": 0,
		} )

		return self.create_build_configuration(object_creator, "Debug", build_settings, "target")

	def create_target_release_configuration_for_library(self, object_creator, name):
		build_settings = self.create_common_target_build_settings_for_library(name)
		return self.create_build_configuration(object_creator, "Release", build_settings, "target")

	def create_target_build_configurations_for_library(self, factory, name):
		build_configurations = [
			self.create_target_debug_configuration_for_library(factory, name),
			self.create_target_release_configuration_for_library(factory, name)
		]

		return build_configurations

	def create_common_project_build_settings(self, header_paths, defines, platform):
		if platform == "ios":
			build_settings = {
				"ARCHS": "$(ARCHS_STANDARD_32_BIT)",
				"GCC_C_LANGUAGE_STANDARD": "c99",
				"GCC_WARN_ABOUT_RETURN_TYPE": "YES",
				"GCC_WARN_UNUSED_VARIABLE": "YES",
				"GCC_THUMB_SUPPORT": "NO",
				"COMPRESS_PNG_FILES": "NO",
				"SDKROOT": "iphoneos",
				"IPHONEOS_DEPLOYMENT_TARGET": 5.1,
				"HEADER_SEARCH_PATHS": header_paths,
				"TARGETED_DEVICE_FAMILY": "1,2"
			}
		elif platform == "mac_os_x":
			build_settings = {
				"ARCHS": "$(ARCHS_STANDARD_32_BIT)",
				"GCC_C_LANGUAGE_STANDARD": "c99",
				"GCC_WARN_ABOUT_RETURN_TYPE": "YES",
				"GCC_WARN_UNUSED_VARIABLE": "YES",
				"GCC_THUMB_SUPPORT": "NO",
				"COMPRESS_PNG_FILES": "NO",
				"SDKROOT": "macosx",
				"HEADER_SEARCH_PATHS": header_paths
			}
		
		build_settings["GCC_PREPROCESSOR_DEFINITIONS"] = defines

		return build_settings

	def create_project_build_settings_for_application(self, header_paths, defines, platform):
		build_settings = self.create_common_project_build_settings(header_paths, defines, platform)
		build_settings["CODE_SIGN_IDENTITY[sdk=iphoneos*]"] = "iPhone Developer"
		return build_settings

	def create_project_release_configuration_for_application(self, object_creator, name, header_paths, defines, platform):
		build_settings = self.create_project_build_settings_for_application(header_paths, defines, platform)
		return self.create_build_configuration(object_creator, "Release", build_settings, "project")

	def create_project_adhoc_configuration_for_application(self, object_creator, name, header_paths, defines, platform):
		build_settings = self.create_project_build_settings_for_application(header_paths, defines, platform)
		build_settings["CODE_SIGN_IDENTITY[sdk=iphoneos*]"] = "iPhone Distribution"
		build_settings["VALIDATE_PRODUCT"] = "YES"
		return self.create_build_configuration(object_creator, "AdHoc", build_settings, "project")

	def create_project_distribution_configuration_for_application(self, object_creator, name, header_paths, defines, platform):
		build_settings = self.create_project_build_settings_for_application(header_paths, defines, platform)
		build_settings["CODE_SIGN_IDENTITY[sdk=iphoneos*]"] = "iPhone Distribution"
		build_settings["VALIDATE_PRODUCT"] = "YES"
		return self.create_build_configuration(object_creator, "AppStore", build_settings, "project")

	def create_project_debug_configuration_for_application(self, object_creator, name, header_paths, defines, platform):
		build_settings = self.create_project_build_settings_for_application(header_paths, defines, platform)
		build_settings["GCC_PREPROCESSOR_DEFINITIONS"] = build_settings["GCC_PREPROCESSOR_DEFINITIONS"]
		build_settings["GCC_OPTIMIZATION_LEVEL"] = "0"
		bc = self.create_build_configuration(object_creator, "Debug", build_settings, "project")
		return bc

	def create_project_build_configurations_for_application(self, factory, name, header_paths, defines, configurations, platform):
		build_configurations = [
			self.create_project_debug_configuration_for_application(factory, name, header_paths, defines + configurations["debug"].defines, platform),
			self.create_project_release_configuration_for_application(factory, name, header_paths, defines + configurations["release"].defines, platform),
			self.create_project_adhoc_configuration_for_application(factory, name, header_paths, defines + configurations["adhoc"].defines, platform),
			self.create_project_distribution_configuration_for_application(factory, name, header_paths, defines + configurations["distribution"].defines, platform),
		]

		return build_configurations

	def create_project_build_settings_for_library(self, header_paths, defines,platform):
		build_settings = self.create_common_project_build_settings(header_paths, defines,platform)
		build_settings["OTHER_LDFLAGS"] = "-ObjC"
		return build_settings

	def create_project_release_configuration_for_library(self, object_creator, name, header_paths, defines, platform):
		build_settings = self.create_project_build_settings_for_library(header_paths, defines,platform)
		return self.create_build_configuration(object_creator, "Release", build_settings, "project")

	def create_project_debug_configuration_for_library(self, object_creator, name, header_paths, defines,platform):
		build_settings = self.create_project_build_settings_for_library(header_paths, defines,platform)
		build_settings["GCC_OPTIMIZATION_LEVEL"] = 0
		return self.create_build_configuration(object_creator, "Debug", build_settings, "project")

	def create_project_build_configurations_for_library(self, factory, name, header_paths, defines,platform):
		build_configurations = [
			self.create_project_debug_configuration_for_library(factory, name, header_paths, defines,platform),
			self.create_project_release_configuration_for_library(factory, name, header_paths, defines,platform)
		]

		return build_configurations

	def create_configuration_list(self, object_creator, build_configurations, usage):
		default_configuration_name = "Release"
		configuration_list = object_creator.create(XCConfigurationList, build_configurations, default_configuration_name, usage)
		self.configuration_lists.append(configuration_list)
		return configuration_list

	def create_target_configuration_list_for_application(self, object_creator, name, plist_filename, library_search_paths, framework_search_paths):
		target_build_configurations = self.create_target_build_configurations_for_application(object_creator, name, plist_filename, library_search_paths, framework_search_paths)
		configuration_list = self.create_configuration_list(object_creator, target_build_configurations, "target")
		return configuration_list

	def create_project_configuration_list_for_application(self, object_creator, name, header_paths, defines, configurations, platform):
		project_build_configurations = self.create_project_build_configurations_for_application(object_creator, name, header_paths, defines, configurations, platform)
		configuration_list = self.create_configuration_list(object_creator, project_build_configurations, "project")
		return configuration_list

	def create_target_configuration_list_for_library(self, object_creator, name):
		target_build_configurations = self.create_target_build_configurations_for_library(object_creator, name)
		configuration_list = self.create_configuration_list(object_creator, target_build_configurations, "target")
		return configuration_list

	def create_project_configuration_list_for_library(self, object_creator, name, header_paths, defines,platform):
		project_build_configurations = self.create_project_build_configurations_for_library(object_creator, name, header_paths, defines,platform)
		configuration_list = self.create_configuration_list(object_creator, project_build_configurations, "project")
		return configuration_list

	def product(self, object_factory, products_group, name, product_type, library_search_paths, framework_search_paths):
		if product_type == "library":
			target_filename = "lib" + name + ".a"
		else:
			target_filename = name + ".app"

		product_file_reference = self.create_file_reference(object_factory, products_group, target_filename)
		build_phases = [self.headers_build_phase, self.resources_build_phase, self.sources_build_phase, self.frameworks_build_phase]
		if product_type == "library":
			target_configuration_list = self.create_target_configuration_list_for_library(object_factory, name)
		else:
			extensions = self.file_references_with_extensions(["plist"])
			if len(extensions) != 0:
				plist_filename = self.file_references_with_extensions(["plist"])[0]
				plist_file_path = FilePath(plist_filename)
			else:
				plist_file_path = ''
			target_configuration_list = self.create_target_configuration_list_for_application(object_factory, name, plist_file_path, library_search_paths, framework_search_paths)


		return object_factory.create(PBXNativeTarget, name, product_file_reference, target_configuration_list, build_phases, product_type)

	def all_source_build_files(self, project):
		return self.build_files_with_extensions(["cpp", "c", "m", "mm"])

	def all_header_build_files(self, project):
		return self.build_files_with_extensions(["pch", "h"])

	def all_resource_build_files(self, project):
		return self.build_files_with_extensions(["xib", "storyboard", "png", "ogg", "oes", "oeb", "oec", "icns", "fnt"])

	def all_resource_file_references(self):
		return self.file_references_with_extensions(["plist", "xib", "storyboard", "png", "ogg", "oes", "oeb", "oec", "icns", "fnt"])

	def file_references_with_extensions(self, extensions_to_match):
		matching_file_references = []
		for file_reference in self.source_file_references:
			filename = file_reference.path
			extension = os.path.splitext(filename)[1][1:]
			if extension in extensions_to_match:
				matching_file_references.append(file_reference)
		return matching_file_references

	def build_files_with_extensions(self, extensions_to_match):
		matching_build_files = []
		for build_file in self.build_files:
			filename = build_file.fileRef.path
			extension = os.path.splitext(filename)[1][1:]
			if extension in extensions_to_match:
				matching_build_files.append(build_file)
		return matching_build_files

	def create_file_reference(self, object_factory, parent_group, filename):
		filename_reference = self.create_invisible_file_reference(object_factory, filename)
		parent_group.append_child(filename_reference)
		return filename_reference

	def create_invisible_file_reference(self, object_factory, filename):
		filename_reference = object_factory.create(PBXFileReference, filename)
		filename_reference.name = os.path.basename(filename)
		self.source_file_references.append(filename_reference)
		return filename_reference		


	def create_build_file(self, object_factory, source_root, filename, root_group):
		parent_group = root_group

		extension = os.path.splitext(filename)[1][1:]
		if extension != "framework" and extension != "dylib":
			parent_group = create_directory_groups(object_factory, root_group, source_root, filename)

		filename_reference = self.create_file_reference(object_factory, parent_group, filename)
		build_file = object_factory.create(PBXBuildFile, filename_reference)
		self.build_files.append(build_file)

		return build_file

	def generate_build_files(self, source_root, source_filenames, extensions, object_factory, root_group):
		for filename in source_filenames:
			extension = os.path.splitext(filename)[1][1:]
			if not extensions or (extension in extensions):
				self.create_build_file(object_factory, source_root, filename, root_group)

	def generate_file_references(self, source_filenames, extensions, object_factory, root_group):
		for filename in source_filenames:
			extension = os.path.splitext(filename)[1][1:]
			if extension in extensions:
				self.create_file_reference(object_factory, root_group, filename)

	def create_default_groups(self):
		pass

class Xcode(XcodeProjectObjectRaw):
	def __init__(self, project, source_root, platform):
		self.archiveVersion = 1
		self.classes = {}
		self.objectVersion = 46
		self.objects = XcodeObjects(project, source_root, platform)
		self.rootObject = self.objects.project
		comment = "Xcode"
		XcodeProjectObjectRaw.__init__(self, project, comment)

	def write(self, creator, name):
		output = creator.create_file(name + ".xcodeproj/project.pbxproj")
		pos = output.target_path.rfind("/", 0, len(output.target_path)-1)
		build_path = output.target_path[:pos]
		self.objects.change_target_path_for_file_references(build_path)
		document = XcodeWriterDocument()
		self.push(document, output)
		
		XcodeProjectObjectRaw.write(self, output)
		document.close(output)
		output.close()
