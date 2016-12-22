from Classes.Conf import Validator
from Classes.Generator import Generator
from pid.decorator import pidfile
from typing import List, Tuple, Any, Dict

import yaml
import sys
import re
import getopt
import os


class InvalidConfigurationException(Exception):
	def __init__(self, filename: str, msg: str) -> None:
		Exception.__init__(self,"Invalid configuration file " + str(filename) + "\n" + msg)


class Program:
	def __init__(self) -> None:
		_initial_path = ""

	@classmethod
	def create(cls) -> 'Program':
		prog = Program()
		prog.init()

		return prog

	def init(self) -> None:
		self._initial_path = os.environ["PATH"]

	def run(self, conf_file: str, optlist: List[Tuple[str, str]]) -> None:
		conf = None
		with open(conf_file) as f:
			conf = yaml.load(f.read())
		if not conf:
			sys.exit(3)

		conf = self.overrided_conf(conf, optlist)
		self.check_conf(conf, conf_file)

		additional_path = conf["path"] if "path" in conf else []
		os.environ["PATH"] = os.pathsep.join(additional_path)+ os.pathsep + self._initial_path

		for map_conf in conf["map"]:
			generator = Generator.create(conf, map_conf)
			generator.generate()

	def check_conf(self, conf: Dict[str, Any], conf_file: str) -> None:
		msg = Validator.is_conf_valid(conf)
		if msg != "":
			raise InvalidConfigurationException(conf_file, msg)

	def overrided_conf(self, conf: Dict[str, Any], opts: List[Tuple[str, str]]) -> Dict[str, Any]:
		# default value
		conf["force"] = False

		# override with opts
		for opt in opts:
			if opt[0] in ("-o", "--output_dir"):
				conf["output_dir"] = opt[1]

			if opt[0] in ("-f"):
				conf["force"] = True

		# add some default values
		for map_conf in conf["map"]:
			if 'max_diff' not in map_conf:
				map_conf['max_diff'] = 20

		return conf

@pidfile()
def main(argv: List[str]) -> None:
	prog = Program.create()
	optlist = [] # type: List[Tuple[str, str]]
	args = [] # type: List[str]
	try:
		optlist, args = getopt.getopt(argv, 'fho:', ["output_dir="])
	except getopt.GetoptError as err:
		print_help()
		sys.exit(2)

	if ("-h", "") in optlist:
		print_help()
		return
	for arg in args:
		prog.run(arg, optlist)

def print_help() -> None:
	print("generate_map.py: generate postfix text map using a configuration file\n"
		  "Options:\n"
		  "  - f: force to generate\n"
		  "  - h: display this help\n"
		  "  - o|output_dir: select output_dir\n"
		  "usage: generate_map.py [-f] [-h] -o|--output_dir dir example.conf example-bis.conf\n")


if __name__ == "__main__":
	main(sys.argv[1:])