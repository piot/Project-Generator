#!/usr/bin/python
from xml.dom import minidom
import xcode
import project_writer
import project

import project_parser
import project_path
import makefile
import visualc

import sys
import os

def usage():
	print("generate -i project_definition -p platform -g project_format\nproject_definition: The xml-file that defines the project\nplatform: iphone, mac_os_x, windows or linux\nproject_format: makefile, visualc or xcode")
	sys.exit(0)

try:
	import getopt
	optlist, list = getopt.getopt(sys.argv[1:], 'p:i:g:', "")
except getopt.GetoptError:
	usage()
	print("called exception")
	sys.exit(1)


class Options:
	def __init__(self):
		self.platform_string = ""
		self.input_filename = ""
		self.generator_name = ""

options = Options()

for option, value in optlist:
	if option == "-p":
		options.platform_string = value
	elif option == "-i":
		options.input_filename = value
	elif option == "-g":
		options.generator_name = value

import os
import platform

def touch(filename):
	if not os.path.exists(filename):
		try:
			os.makedirs(os.path.dirname(filename))
		except os.error as e:
			import errno
			if e.errno != errno.EEXIST:
				raise
		open(filename, 'w').close()

def create_project(filename, platform_string):
	target_project = project.Project(platform_string)

	parser = project_parser.Parser()
	node = minidom.parse(filename)

	source_root = os.path.abspath(os.path.dirname(filename)) + "/"
	parser.parse(node, target_project, source_root, platform_string)
	if target_project.target_type != "library":
		resource_root = os.path.normpath(os.path.join(source_root, "../data")) + "/"
		target_project.add_resource_directory(resource_root, False, [])

		resource_root = os.path.normpath(os.path.join(source_root, "../resources")) + "/" + platform_string + "/"
		print("resource:", resource_root);
		target_project.add_resource_directory(resource_root, False, [])


	return target_project


def load_project(filename, platform_string):
	target_project = create_project(filename, platform_string)
	for dependency in target_project.dependencies():
		if not dependency.merge:
			raise "Not supported!!"

		p = load_project(dependency.filename, platform_string)
		target_project.merge(p)

	return target_project

def get_class( kls ):
	parts = kls.split('.')
	module = ".".join(parts[:-1])
	m = __import__( module )
	for comp in parts[1:]:
	    m = getattr(m, comp)
	return m

target_project = load_project(options.input_filename, options.platform_string)
source_root = os.path.abspath(os.path.dirname(options.input_filename)) + "/"
source_root = source_root.replace("\\", "/")

build_dir = project_path.Path(source_root).join("../build/" + options.platform_string + "/")
build_dir = build_dir.replace("\\", "/")

target_filename_prefix = build_dir

if options.generator_name == "xcode":
	generator_name = "xcode.Xcode"
	target_filename = target_filename_prefix + target_project.name() + ".xcodeproj/project.pbxproj"
elif options.generator_name == "makefile":
	target_filename = target_filename_prefix + "Makefile"
	generator_name = "makefile.Makefile"
	platform_specific_library_search_path = project_path.Path(source_root).join("../external/lib/" + options.platform_string + "/")
	target_project.library_search_paths.append(platform_specific_library_search_path)
elif options.generator_name == "visualc":
	target_filename = target_filename_prefix + target_project.name() + ".vcxproj"
	generator_name = "visualc.VisualC"

generator = get_class(generator_name)(target_project, source_root, options.platform_string)
generator.change_short_name_for_file_references(source_root)

if options.platform_string == "iphone" or options.platform_string == "mac_os_x":
	touch(build_dir + target_project.name() + "_Prefix.pch")

output = project_writer.ProjectFileOutput(target_filename)
generator.write(output)
generator.close(output)
output.close()
