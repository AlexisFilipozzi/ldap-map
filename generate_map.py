from Classes.Bind import Bind
from Classes.LDAPReader import LDAPReader
from Classes.Conf import Validator
from Classes.Generator import Generator
from Classes.CheckStrategy import DiffCheckerStrategy, WriterStrategy
import yaml
import sys
import re


class InvalidConfigurationException(Exception):
	def __init__(self, filename):
		Exception.__init__(self,"Invalid configuration file " + str(filename))


class Program:
	@staticmethod
	def run(conf_file):
		conf = None
		with open(conf_file) as f:
			conf = yaml.load(f.read())
		if not conf:
			return
		if not Validator.is_conf_valid(conf):
			raise InvalidConfigurationException(conf_file)

		bind = Program.create_bind(conf)
		for map_conf in conf["map"]:
			attr = Generator.attribute_from_template_string(map_conf["template"])
			if "result_filter_template" in map_conf:
				attr += Generator.attribute_from_template_string(map_conf["result_filter_template"])
			ldap_reader = LDAPReader(bind, map_conf["baseDN"], map_conf["filter"], attr)
			ldap_reader.read()
			generator = Generator(map_conf, conf["diff_ckeck"] if "diff_ckeck" in conf.keys() else None)
			if "diff_ckeck" in conf.keys():
				generator.add_strategy(DiffCheckerStrategy())
			generator.add_strategy(WriterStrategy())
			data = ldap_reader.get_list_dict_from_result()
			generator.set_data(data)
			generator.generate(conf["postmap_cmd"])
			print("file " + str(map_conf["file"]) + " has been generated")

	@staticmethod
	def create_bind(conf):
		return Bind(conf["bind"]["name"], conf["bind"]["password"], conf["bind"]["address"])


def main(argv):
	for arg in argv:
		Program.run(arg)


if __name__ == "__main__":
	main(sys.argv[1:])