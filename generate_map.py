from Classes.Conf import Validator
from Classes.Generator import Generator
from Classes.CheckStrategy import DiffCheckerStrategy
import yaml
import sys
import re


class InvalidConfigurationException(Exception):
	def __init__(self, filename):
		Exception.__init__(self,"Invalid configuration file " + str(filename))


class Program:
	# TODO multiple LDAP request for one file (il faut faire plusieurs appel LDAP et donc déplacer l'appel au LDAP)
	@staticmethod
	def run(conf_file):
		conf = None
		with open(conf_file) as f:
			conf = yaml.load(f.read())
		if not conf:
			return
		if not Validator.is_conf_valid(conf):
			raise InvalidConfigurationException(conf_file)

		for map_conf in conf["map"]:
			generator = Generator(conf, map_conf)
			if "diff_ckeck" in conf.keys():
				generator.add_strategy(DiffCheckerStrategy())
			generator.generate(conf["postmap_cmd"])
			print("file " + str(map_conf["file"]) + " has been generated")



def main(argv):
	for arg in argv:
		Program.run(arg)


if __name__ == "__main__":
	main(sys.argv[1:])