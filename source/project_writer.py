import os

class ProjectFileCreator:
	def __init__(self, prefix):
		self.prefix = prefix

	def create_file(self, name):
		return ProjectFileOutput(self.prefix + name)

class ProjectOutput:
	def __init__(self):
		self.tab_count = 0

	def output(self, s):
		self.write(self.__output_tabs() + s + "\n")

	def output_no_lf(self, s):
		self.write(s)

	def increase_tabs(self):
		self.tab_count += 1

	def decrease_tabs(self):
		self.tab_count -= 1

	def __output_tabs(self):
		s = ""
		for x in range(0, self.tab_count):
			s = s + "\t"
		return s

class ProjectFileOutput(ProjectOutput):
	def __init__(self, filename):
		ProjectOutput.__init__(self)
		import errno
		try:
			os.makedirs(os.path.dirname(filename))
		except os.error as e:
			if e.errno != errno.EEXIST:
				raise
		self.file = open(filename, 'w')
		self.target_path = os.path.dirname(filename) + "/"
		print("Writing to file:", self.target_path)

	def close(self):
		self.file.close()

	def write(self, s):
		self.file.write(s)

class ProjectWriter:
	def __init__(self):
		self.stack = []

	def write(self, output):
		pass

	def close(self, output):
		while len(self.stack) > 0:
			o = self.stack.pop()
			o.close(output)

	def push(self, object, output):
		self.stack.append(object)
		object.write(output)
