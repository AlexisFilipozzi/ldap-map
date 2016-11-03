import os
import difflib
from Classes.Mailer import Mailer
from typing import List


if False:
    # for forward-reference type-checking:
    from Classes.Generator import Generator


class InvalidFileException(Exception):
	def __init__(self, filename: str) -> None:
		Exception.__init__(self, "Unable to open file " + filename)


class CheckStrategy:
	def handle_file(self, new_file_content: List[str], generator: 'Generator', force: bool) -> bool:
		# return True if the file is not ok, and thus will not be generated
		return False


class DiffCheckerStrategy(CheckStrategy):
	def get_max_diff(self, generator: 'Generator'):
		return generator.map_conf()['max_diff']

	def handle_file(self, new_file_content: List[str], generator: 'Generator', force: bool) -> bool:
		if not self.old_file_exist(generator):
			# the file doesn't exist, there is no diff to check
			return False

		old_lines = [] # type: List[str]
		try:
			old_lines = self.get_old_file_content(generator)
		except InvalidFileException as e:
			return False

		diff = difflib.Differ().compare(new_file_content, old_lines)
		nb_diff = 0
		for d in diff:
			code = d[:2]
			if code in [ "+ ", "- "]:
				nb_diff += 1
		if nb_diff > self.get_max_diff(generator):
			if force:
				print("Trop de changement dans la table %s, cette table sera tout de même générée." % self.filename(generator))
				return False
			else:
				print("sending mail", force)
				self.send_mail(generator)

				print("The file %s has NOT been generated due to too much change, to generate it anyway use the flag -f" % self.filename(generator))
				return True
		return False

	def send_mail(self, generator: 'Generator') -> None:
		mail_send = True
		smtp_conf = generator.smtp_conf()
		if (not smtp_conf):
			# even when there is too much diff we generate the file, so there is no need to check
			mail_send =  False

		if mail_send:
			mailer = Mailer.get_instance()
			msg = "A cause d'un trop grand nombre de modifications dans la génération de la table %s, cette table n'a pas été regénérée. Pour la regénérer, réexécutez le script de génération de table en utilisant le flag -f." % generator.map_conf()["file"]
			subject = "Trop de modification dans la génération de table Postfix"
			from_who = smtp_conf["sender"]
			to = smtp_conf["recipient"]
			smtp = smtp_conf["smtp_server"]

		mail_send = mailer.send_mail(from_who, to, subject, msg, smtp)

		if not mail_send:
			print("No mail has been sent")

	def get_old_file_content(self, generator: 'Generator') -> List[str]:
		with open(self.filename(generator)) as f:
			return f.readlines()
		raise InvalidFileException(self.filename(generator))

	def old_file_exist(self, generator: 'Generator') -> bool:
		return os.path.isfile(generator.map_conf()["file"])

	def filename(self, generator: 'Generator') -> str:
		return generator.path_of_file_to_generate()