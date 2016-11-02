import os
import difflib
from Classes.Mailer import Mailer

class Generator:
	pass

class CheckStrategy:
	def handle_file(self, new_file_content: str, generator: Generator, force: bool) -> bool:
		# return True if the generated file has been handled (next MapFileStrategy will not be called)
		return False


class DiffCheckerStrategy(CheckStrategy):
	def get_max_diff(self, generator: Generator):
		return generator.map_conf()['max_diff']

	def handle_file(self, new_file_content: str, generator: Generator, force: bool) -> bool:
		if not os.path.isfile(generator.map_conf()["file"]):
			# the file doesn't exist, there is no diff to check
			return False

		smtp_conf = generator.smtp_conf()
		if (not smtp_conf):
			# even when there is too much diff we generate the file, so there is no need to check
			return False

		with open(generator.path_of_file_to_generate()) as f:
			old_lines = f.readlines()
			diff = difflib.Differ().compare(new_file_content, old_lines)
			nb_diff = 0
			for d in diff:
				code = d[:2]
				if code in [ "+ ", "- "]:
					nb_diff += 1
			if nb_diff > self.get_max_diff(generator):
				if force:
					print("Trop de changement dans la table %s, cette table sera tout de même générée." % generator.map_conf()["file"])
					return False
				else:
					mailer = Mailer.get_instance()
					msg = "A cause d'un trop grand nombre de modifications dans la génération de la table %s, cette table n'a pas été regénérée. Pour la regénérer, réexécutez le script de génération de table en utilisant le flag -f." % generator.map_conf()["file"]
					subject = "Trop de modification dans la génération de table Postfix"
					from_who = smtp_conf["sender"]
					to = smtp_conf["recipient"]
					smtp = smtp_conf["smtp_server"]
				
					if not mailer.send_mail(from_who, to, subject, msg, smtp):
						print("No mail has been sent")

					print("The file %s has NOT been generated due to too much change, to generate it anyway use the flag -f" % generator.map_conf()["file"])
					return True
		return False
