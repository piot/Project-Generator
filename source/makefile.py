import project_writer
import os
import project_path
import re

class Makefile:
	def __init__(self, project, source_root, platform):
		self.output = None
		self.project = project
		self.source_root = source_root

	def output_variable(self, variable, content):
		self.output.output(variable + " = " + content)
		self.output.output("")

	def output_variable_list(self, variable, contents):
		s = ""
		for content in contents:
			s = s + " " + content

		self.output_variable(variable, s)

	def output_target_dependency(self, target, dependency):
		self.output.output(target + ": " + dependency)
		self.output.increase_tabs()

	def output_target_dependencies(self, target, dependencies, commands):
		self.output.output("")
		s = ""
		for dependency in dependencies:
			s = s + " " + dependency

		self.output_target_dependency(target, s)
		for command in commands:
			self.output_command(command)
		self.output.decrease_tabs()

	def output_command(self, command):
		self.output.output(command)

	def change_extension(self, filename, new_extension):
		return file_without_extension + "." + new_extension

	def write(self, creator, name):
		self.output = creator.create_file("/Makefile")

		complete_sources = self.project.settings.source_filenames()
		objects = []
		sources = []

		for source in complete_sources:
			path = project_path.Path(source)
			relative_source = path.relative(self.source_root)
			file_without_extension, extension = os.path.splitext(relative_source)
			if extension == ".cpp" or extension == ".c":
				sources.append(relative_source)
				objects.append(file_without_extension + ".o")

		includes = self.project.settings.include_paths()
		include_string = " -I" + " -I".join(includes)

		define_string = "-D" + " -D".join(self.project.configurations["debug"].defines + self.project.settings.defines)

		if self.project.settings.library_filenames:
			link_string = "-l" + " -l".join(self.project.settings.library_filenames)
		else:
			link_string = "";

		if self.project.settings.framework_names:
			link_string += "-framework " + " -framework ".join(self.project.settings.framework_names)

		compiler_executable = self.project.settings.compiler_executable or "g++"
		self.output_variable_list("cc", [compiler_executable])
		self.output_variable_list("c", [ compiler_executable, "-x c"])

		compiler_flags = self.project.settings.compiler_flags + ["-Wall", "-Wextra -Werror -Wno-unused-parameter -Wno-missing-field-initializers -std=c99 -pedantic"]
		flags_array = ["-c", define_string, include_string]
		flags_array.extend(compiler_flags)
		self.output_variable_list("cflags", flags_array)

		linker_flags = self.project.settings.linker_flags or "";
		self.output_variable_list("ldflags", [link_string])

		self.output_variable_list("sources", sources)
		self.output_variable_list("objects", objects)
		self.output_variable_list("executable", [self.project.target_name + ".out"])

		self.output_target_dependencies("all", [self.project.target_name], [])
		self.output_target_dependencies("clean", "", ["@rm -f $(objects)", "@echo clean done!"])
		self.output_target_dependencies(self.project.target_name, ["$(sources) $(executable)"], ["@echo 'done'"])
		self.output_target_dependencies("-include $(objects:.o=.d)", [], [])
		self.output_target_dependencies("$(executable)", ["$(objects)"], ["@echo Linking $@", "@$(cc) -o $@  $(objects) $(ldflags)"])
		self.output_target_dependencies(".c.o", [], ["echo Compiling c $@", "@$(c) $(cflags) $< -o $@"])
		self.output_target_dependencies(".cpp.o", [], ["echo Compiling c++ $@", "@$(cc) $(cflags) $< -o $@"])
		self.output_target_dependencies("depend", [], ["makedepend -f " + self.output.target_path + "Makefile -- $(cflags) -- $(sources) -I" + include_string])
		self.close()
		self.output.close()

	def close(self):
		self.output.output("# DO NOT DELETE")
		pass
