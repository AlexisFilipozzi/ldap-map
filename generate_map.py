from Classes.Conf import Validator
from Classes.Generator import Generator

import yaml
import sys
import re
import getopt
import os

class InvalidConfigurationException(Exception):
	def __init__(self, filename, msg):
		Exception.__init__(self,"Invalid configuration file " + str(filename) + "\n" + msg)


class Program:
	_initial_path = ""

	@classmethod
	def init(cls):
		cls._initial_path = os.environ["PATH"]

	@classmethod
	def run(cls, conf_file, optlist):
		conf = None
		with open(conf_file) as f:
			conf = yaml.load(f.read())
		if not conf:
			return

		Program.check_conf(conf, conf_file)

		additional_path = conf["path"] if "path" in conf else []
		os.environ["PATH"] = os.pathsep.join(additional_path)+ os.pathsep + cls._initial_path

		for map_conf in conf["map"]:
			generator = Generator.create(conf, map_conf, optlist)
			generator.generate()

	@staticmethod
	def check_conf(conf, conf_file):
		msg = Validator.is_conf_valid(conf)
		if msg != "":
			raise InvalidConfigurationException(conf_file, msg)


def main(argv):
	Program.init()
	optlist, args = getopt.getopt(argv, 'fh')
	if ("-h", "") in optlist:
		self.print_help()
		return
	for arg in args:
		Program.run(arg, optlist)

def print_help(self):
	print("generate_map.py: generate postfix text map using a configuration file\n"
		  "Options:\n"
		  "  - f: force to generate\n"
		  "  - h: display this help\n"
		  "usage: generate_map.py [-f] [-h] example.conf example-bis.conf\n")


if __name__ == "__main__":
	main(sys.argv[1:])