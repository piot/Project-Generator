import os
import glob
import project_path

class SourceFileNode:
	def __init__(self):
		self.filenames = []

	def search_recursive(self, dor, extensions, exclude_basenames):
		for path, dirs, files in os.walk(dor + "/"):
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
		filenames = glob.glob(dor + "*")
		for filename in filenames:
			
			filename = filename.replace("\\", "/")
			basename = os.path.basename(filename)

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

class Project:
	def __init__(self, platform_string):
		self.header_paths = []
		self.library_filenames = []
		self.root_source_files = SourceFileNode()
		self.root_resource_files = SourceFileNode()
		self.library_search_paths = []
		self.platform_string = platform_string
		self.target_name = None
		self.defines = []
		self.dependency_projects = []

	def merge(self, p):
		self.header_paths.extend(p.header_paths)
		self.library_filenames.extend(p.library_filenames)
		self.root_source_files.filenames.extend(p.root_source_files.filenames)
		self.library_search_paths.extend(p.library_search_paths)
		self.defines.extend(p.defines)
		assert(self.platform_string == p.platform_string)

	def add_dependency(self, filename, merge):
		self.dependency_projects.append(Dependency(filename, merge))
		
	def add_define(self, name):
		self.defines.append(name)

	def dependencies(self):
		return self.dependency_projects
		
	def set_name(self, name):
		self.target_name = name

	def set_target_type(self, target_type):
		self.target_type = target_type

	def name(self):
		return self.target_name

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
		extensions = ["png", "oes", "oeb", "oec", "jpg", "ogg", "icns", "plist"]
		if recursive:
			self.root_resource_files.search_recursive(path, extensions, exclude_list)
		else:
			self.root_resource_files.search_directory_only(path, extensions, exclude_list)

	def resource_filenames(self):
		return self.root_resource_files.source_filenames()

	def source_filenames(self):
		return self.root_source_files.source_filenames()

	def add_library_filename(self, library_filename):
		self.library_filenames.append(library_filename)

	def add_library_search_path(self, path):
		library_path = path + self.platform_string + "/"
		self.library_search_paths.append(library_path)

	def include_paths(self):
		return self.header_paths
