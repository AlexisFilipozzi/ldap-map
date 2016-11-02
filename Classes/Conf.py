from typing import Dict, Any

class Validator:
	@staticmethod
	def is_conf_valid(conf: Dict[str, Any]) -> str:
		if not "bind" in conf:
			return "bind is missing"
		if not "name" in conf["bind"]:
			return "bind name is missing"
		if not "address" in conf["bind"]:
			return "bind address is missing"
		if not "password" in conf["bind"]:
			return "bind password is missing"

		if not "postmap_cmd" in conf:
			return "postmap command is missing"

		if not "output_dir" in conf:
			return "output_dir missing"

		if not "map" in conf:
			return "map attribute is missing"
		for m in conf["map"]:
			msg = Validator.is_map_conf_valid(m)
			if msg != "":
				return msg

		if "smtp" in conf:
			if not "sender" in conf["smtp"]:
				return "smtp-sender is missing"
			if not "smtp_server" in conf["smtp"]:
				return "smtp-server is missing"
			if not "recipient" in conf["smtp"]:
				return "smtp recipient list is missing"

		return ""


	@staticmethod
	def is_map_conf_valid(map_conf: Any) -> str:
		if not "file" in map_conf:
			return "map file name is missing"
		filename = str(map_conf["file"])
		if not "request" in map_conf:
			return "map request is missing for map " + filename
		for r in map_conf["request"]:
			msg = Validator.is_request_conf_valid(r)
			if msg != "":
				return msg + " for map " + filename
		return ""

	@staticmethod
	def is_request_conf_valid(request_conf: Any) -> str:
		if not "filter" in request_conf:
			return "request filter is missing"
		if not "key_template" in request_conf:
			return "key_template is missing"
		if not "value_template" in request_conf:
			return "value_template is missing"
		if not "baseDN" in request_conf:
			return "baseDN is missing"
		return ""
