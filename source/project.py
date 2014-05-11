import os
import glob
import project_path

class SourceFileNode:
	def __init__(self):
		self.filenames = []

	def extend(self, other):
		self.filenames.extend(other.filenames)

	def search_recursive(self, dor, extensions, exclude_basenames):
		# print("BaseName rec:", dor)
		for path, dirs, files in os.walk(dor):
			for filename in files:
				filename = os.path.abspath(os.path.join(path, filename))
				filename = filename.replace("\\", "/")

				basename = os.path.basename(filename)

				if basename in exclude_basenames:
					continue
				extension = os.path.splitext(filename)[1][1:]
				if extension in extensions:
					complete_path = filename
					self.filenames.append(complete_path)

	def search_directory_only(self, dor, extensions, exclude_basenames):
		# print("BaseName:", dor + "*")
		filenames = glob.glob(dor + "*")
		for filename in filenames:
			filename = filename.replace("\\", "/")
			basename = os.path.basename(filename)

			# print("filename:", filename, "BaseName:", basename)
			if basename in exclude_basenames:
				continue

			extension = os.path.splitext(filename)[1][1:]
			if extension in extensions:
				complete_path = filename
				self.filenames.append(complete_path)

		self.filenames.sort()

	def source_filenames(self):
		return self.filenames

class Dependency:
	def __init__(self, filename, merge):
		self.filename = filename
		self.merge = merge

class Define:
	def __init__(self, name):
		self.name = name

class Settings(object):
	def __init__(self):
		self.defines = []
		self.header_paths = []
		self.root_source_files = SourceFileNode()
		self.library_search_paths = []
		self.library_filenames = []
		self.framework_names = []
		self.framework_search_paths = []
		self.root_resource_files = SourceFileNode()
		self.compiler_executable = None
		self.compiler_flags = []
		self.linker_flags = []

	def extend(self, setting):
		self.defines.extend(setting.defines)
		self.header_paths.extend(setting.header_paths)
		self.root_source_files.extend(setting.root_source_files)
		self.library_search_paths.extend(setting.library_search_paths)
		self.library_filenames.extend(setting.library_filenames)
		self.framework_names.extend(setting.framework_names)
		self.framework_search_paths.extend(setting.framework_search_paths)
		self.root_resource_files.extend(setting.root_resource_files)
		self.compiler_executable = self.compiler_executable or setting.compiler_executable
		self.compiler_flags.extend(setting.compiler_flags)
		self.linker_flags.extend(setting.linker_flags)

	def add_define(self, name):
		self.defines.append(name)

	def add_header_directory(self, path):
		self.header_paths.append(path)
		header_extensions = ["h", "hpp"]
		empty_exclude_list = []
		self.root_source_files.search_recursive(path, header_extensions, empty_exclude_list)

	def add_source_directory(self, path, recursive, exclude_list):
		extensions = ["cpp", "c", "h", "pch", "xib", "m", "mm"]
		if recursive:
			self.root_source_files.search_recursive(path, extensions, exclude_list)
		else:
			self.root_source_files.search_directory_only(path, extensions, exclude_list)

	def add_resource_directory(self, path, recursive, exclude_list):
		extensions = ["png", "xib", "storyboard", "oes", "oeb", "oec", "jpg", "ogg", "icns", "plist"]
		if recursive:
			self.root_resource_files.search_recursive(path, extensions, exclude_list)
		else:
			self.root_resource_files.search_directory_only(path, extensions, exclude_list)

	def resource_filenames(self):
		return self.root_resource_files.source_filenames()

	def source_filenames(self):
		return self.root_source_files.source_filenames()

	def add_library_filename(self, library_filename):
		if library_filename[-10:] == ".framework":
			self.framework_names.append(library_filename[:-10])
		else:
			self.library_filenames.append(library_filename)

	def add_library_search_path(self, path):
		self.library_search_paths.append(path)

	def add_framework_search_path(self, path):
		self.framework_search_paths.append(path)

	def set_compiler(self, compiler, flags):
		self.compiler_executable = compiler
		self.compiler_flags = flags.split(" ")

	def set_linker(self, linker, flags):
		self.linker_executable = linker
		self.linker_flags = flags

	def include_paths(self):
		return self.header_paths

class Configuration(Settings):
	def __init__(self, name):
		super(Configuration, self).__init__()
		self.name = name

class Project:
	def __init__(self, platform_string):
		self.platform_string = platform_string
		self.target_name = None
		self.dependency_projects = []
		self.configurations = {}
		self.settings = Settings()

	def add_configuration(self, name):
		config = Configuration(name)
		self.configurations[name] = config
		return config

	def configuration(self, name):
		if name in self.configurations:
			return self.configurations[name]
		else:
			return self.add_configuration(name)

	def settings(self):
		return self.settings

	def merge(self, p):
		self.settings.extend(p.settings)
		assert(self.platform_string == p.platform_string)
		self.configurations = p.configurations

	def add_dependency(self, filename, merge):
		self.dependency_projects.append(Dependency(filename, merge))

	def dependencies(self):
		return self.dependency_projects

	def set_name(self, name):
		self.target_name = name

	def set_target_type(self, target_type):
		self.target_type = target_type

	def name(self):
		return self.target_name
