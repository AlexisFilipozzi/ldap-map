class Validator:
	@staticmethod
	def is_conf_valid(conf):
		if not "bind" in conf:
			return False
		if not "name" in conf["bind"]:
			return False
		if not "address" in conf["bind"]:
			return False
		if not "password" in conf["bind"]:
			return False

		if not "postmap_cmd" in conf:
			return False

		if not "map" in conf:
			return False
		for m in conf["map"]:
			if not Validator.is_map_conf_valid(m):
				return False

		if "smtp" in conf:
			if not "sender" in conf["smtp"]:
				return False
			if not "smtp_server" in conf["smtp"]:
				return False
			if not "recipient" in conf["smtp"]:
				return False
		return True


	@staticmethod
	def is_map_conf_valid(map_conf):
		if not "file" in map_conf:
			return False
		if not "request" in map_conf:
			return False
		for r in map_conf["request"]:
			if not Validator.is_request_conf_valid(r):
				return False
		return True

	@staticmethod
	def is_request_conf_valid(request_conf):
		if not "filter" in request_conf:
			return False
		if not "key_template" in request_conf:
			return False
		if not "value_template" in request_conf:
			return False
		if not "baseDN" in request_conf:
			return False
		return True
