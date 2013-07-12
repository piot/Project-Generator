#!/usr/bin/python
from xml.dom import minidom
import xcode
import project_writer
import project

import project_parser
import project_path
import makefile
import visualc
import codeblocks
import codelite

import sys
import os

def usage():
	print("generate -i project_definition -p platform -g project_format\nproject_definition: The xml-file that defines the project\nplatform: iphone, mac_os_x, windows or linux\nproject_format: makefile, visualc, xcode, codelite, codeblocks")
	sys.exit(0)

try:
	import getopt
	optlist, list = getopt.getopt(sys.argv[1:], 'p:i:g:d:n:r:o:', "")
except getopt.GetoptError:
	usage()
	print("called exception")
	sys.exit(1)

class Options:
	def __init__(self):
		self.platform_string = ""
		self.input_filename = ""
		self.generator_name = ""
		self.data_path = ""
		self.resource_path = ""
		self.project_name = ""
		self.target_path = ""

options = Options()

for option, value in optlist:
	if option == "-p":
		options.platform_string = value
	elif option == "-i":
		options.input_filename = value
	elif option == "-g":
		options.generator_name = value
	elif option == "-d":
		options.data_path = os.path.abspath(value)
	elif option == "-r":
		options.resource_path = os.path.abspath(value)
	elif option == "-n":
		options.project_name = value
	elif option == "-o":
		options.target_path = os.path.abspath(value)

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

def create_project(filename, platform_string, data_path, resource_path):
	target_project = project.Project(platform_string)
	parser = project_parser.Parser()
	node = minidom.parse(filename)

	source_root = os.path.abspath(os.path.dirname(filename)) + "/"
	parser.parse(node, target_project, source_root, platform_string)
	if target_project.target_type != "library":
		if data_path != None:
			resource_root = os.path.normpath(data_path) + "/"
			# print("data:", resource_root)
			target_project.settings.add_resource_directory(resource_root, False, [])

		resource_root = os.path.normpath(resource_path) + "/" + platform_string + "/"
		# print("Resource:", resource_root)
		target_project.settings.add_resource_directory(resource_root, False, [])


	return target_project

def load_project(filename, platform_string, data_path, resource_path):
	target_project = create_project(filename, platform_string, data_path, resource_path)
	for dependency in target_project.dependencies():
		if not dependency.merge:
			raise "Not supported!!"

		p = load_project(dependency.filename, platform_string, data_path, resource_path)
		target_project.merge(p)

	return target_project

def get_class( kls ):
	parts = kls.split('.')
	module = ".".join(parts[:-1])
	m = __import__( module )
	for comp in parts[1:]:
	    m = getattr(m, comp)
	return m

if options.project_name == "":
	print("Must specify project name")
	exit(-1)

target_project = load_project(options.input_filename, options.platform_string, options.data_path, options.resource_path)

if options.project_name != "":
	target_project.set_name(options.project_name)

source_root = os.path.abspath(os.path.dirname(options.input_filename)) + "/"
source_root = source_root.replace("\\", "/")

build_dir = options.target_path + "/" + options.platform_string + "/"
build_dir = build_dir.replace("\\", "/")

target_filename_prefix = build_dir
project_file_name_prefix = options.project_name

if options.generator_name == "xcode":
	generator_name = "xcode.Xcode"
elif options.generator_name == "makefile":
	generator_name = "makefile.Makefile"
elif options.generator_name == "visualc":
	generator_name = "visualc.VisualC"
elif options.generator_name == "codeblocks":
	generator_name = "codeblocks.CodeBlocks"
elif options.generator_name == "codelite":
	generator_name = "codelite.CodeLite"

generator = get_class(generator_name)(target_project, source_root, options.platform_string)

if options.platform_string == "ios" or options.platform_string == "mac_os_x":
	touch(build_dir + target_project.name() + "_Prefix.pch")

creator = project_writer.ProjectFileCreator(target_filename_prefix)
generator.write(creator, project_file_name_prefix)
