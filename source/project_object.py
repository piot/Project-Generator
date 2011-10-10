import project_writer
import os

def add_quotation_marks_when_needed(value):
	value = '"' + value + '"'
	return value

class WriterAttribute(project_writer.ProjectWriter):
	def __init__(self, keyword, value):
		project_writer.ProjectWriter.__init__(self)
		self.keyword = keyword
		self.value = value

	def write(self, output):
		keyword = self.keyword
		value = add_quotation_marks_when_needed(self.value)
		output.output_no_lf(keyword + " = " + value + " ")

class WriterScope(project_writer.ProjectWriter):
	def __init__(self, keyword):
		project_writer.ProjectWriter.__init__(self)
		self.keyword = keyword

	def write(self, output):
		output.output("<" + str(self.keyword) + ">")
		output.increase_tabs()

	def close(self, output):
		project_writer.ProjectWriter.close(self, output)
		output.decrease_tabs()
		output.output( "<" + str(self.keyword) + " />" )

class WriterList(project_writer.ProjectWriter):
	def __init__(self, ids):
		project_writer.ProjectWriter.__init__(self)
		self.ids = ids

	def write(self, output):
		for id_object in self.ids:
			output_value(id_object, output)

	def close(self, output):
		pass

class WriterDictionary(project_writer.ProjectWriter):
	def __init__(self, dictionary):
		project_writer.ProjectWriter.__init__(self)
		self.dictionary = dictionary

	def write(self, output):
		project_writer.ProjectWriter.write(self, output)
		for name in sorted(self.dictionary.keys()):
			value = self.dictionary[name]
			output.output("<" + name + ">" + value + "</" + name + ">")

def output_value(value, output):
	if isinstance(value, list):
		write_object = WriterList(value)
	elif isinstance(value, dict):
		write_object = WriterDictionary(value)
	else:
		write_object = value

	write_object.write(output)
	write_object.close(output)

class WriterObject(project_writer.ProjectWriter):
	def write_all_attributes(self, output, exclude_object = None):
		for name in sorted(self.__dict__.keys()):
			if exclude_object != None:
				exclude_properties = exclude_object.__dict__.keys()

				if name in exclude_properties:
					continue

			value = self.__dict__[name]
			output_value( value, output)

	def add_properties(self):
		s = ""
		for name in sorted(self.__dict__.keys()):
			value = self.__dict__[name]
			if not isinstance(value, list) and not  isinstance(value, dict):
				s = s + " " + name + '="' + value + '" '
		return s

	def write_all_lists(self, output):
		for name in sorted(self.__dict__.keys()):
			value = self.__dict__[name]
			if isinstance(value, list):
				output_value(value, output)

	def write_all_dictionaries(self, output):
		for name in sorted(self.__dict__.keys()):
			value = self.__dict__[name]
			if isinstance(value, dict):
				output_value(value, output)

	def name(self):
		return self.__class__.__name__

	def has_children(self):
		for name in sorted(self.__dict__.keys()):
			value = self.__dict__[name]
			if isinstance(value, dict) or isinstance(value, list):
				return True
		return False

	def write(self, output):
		s = "<" + self.name()
		s = s + self.add_properties()
		if self.has_children():
			s = s + ">"
			output.output(s)
			output.increase_tabs()
			self.write_all_lists(output)
			self.write_all_dictionaries(output)
		else:
			s = s + "/>"
			output.output(s)

	def close(self, output):
		if self.has_children():
			s = "</" + self.name() + ">"
			output.decrease_tabs()
			output.output(s)
