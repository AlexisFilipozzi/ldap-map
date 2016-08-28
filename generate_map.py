from Classes.Conf import Validator
from Classes.Generator import Generator
from Classes.CheckStrategy import DiffCheckerStrategy
import yaml
import sys
import re
import getopt


class InvalidConfigurationException(Exception):
	def __init__(self, filename):
		Exception.__init__(self,"Invalid configuration file " + str(filename))


class Program:
	@staticmethod
	def run(conf_file, optlist):
		conf = None
		with open(conf_file) as f:
			conf = yaml.load(f.read())
		if not conf:
			return
		if not Validator.is_conf_valid(conf):
			raise InvalidConfigurationException(conf_file)

		for map_conf in conf["map"]:
			generator = Generator(conf, map_conf, optlist)
			if "diff_ckeck" in conf.keys():
				generator.add_strategy(DiffCheckerStrategy())
			generator.generate(conf["postmap_cmd"])



def main(argv):
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