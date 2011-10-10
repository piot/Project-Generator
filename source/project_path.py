import os

class Path:
	def __init__(self, path_string):
		self.path_string = path_string

	def _relpath(self, target, base=os.curdir):
		if not os.path.exists(target):
			raise OSError('Target does not exist: '+target)

		if not os.path.isdir(base):
			raise OSError( 'Base is not a directory or does not exist: '+base)

		base_list = (os.path.abspath(base)).split(os.sep)
		target_list = (os.path.abspath(target)).split(os.sep)

		if os.name in ['nt','dos','os2'] and base_list[0] != target_list[0]:
			raise OSError('Target is on a different drive to base. Target: '+target_list[0].upper()+', base: '+base_list[0].upper())

		for i in range(min(len(base_list), len(target_list))):
			if base_list[i] != target_list[i]: break
		else:
			i+=1

		rel_list = [os.pardir] * (len(base_list)-i) + target_list[i:]
		return os.path.join(*rel_list)

	def join(self, path_string):
		new_path = os.path.normpath(os.path.join(self.path_string, path_string)) + "/"
		return new_path

	def relative(self, start_path_string):
		new_path = self._relpath(self.path_string, start_path_string)
		new_path = new_path.replace("\\", "/")
		return new_path
