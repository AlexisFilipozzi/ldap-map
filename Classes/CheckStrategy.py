from email.mime.text import MIMEText
import os
import difflib
import smtplib


class CheckStrategy:
	def handle_file(self, new_file_content, generator):
		# return True if the generated file has been handled (next MapFileStrategy will not be called)
		return False


class DiffCheckerStrategy(CheckStrategy):
	def handle_file(self, new_file_content, generator):
		if not os.path.isfile(generator._map_name):
			# the file doesn't exist, there is no diff to check
			return False

		diff_check_conf = generator.diff_checks()
		if (not diff_check_conf) or diff_check_conf["generate_if_diff"]:
			# even when there is too much diff we generator, the file, so there is no need to check
			return False

		with open(generator._map_name) as f:
			old_lines = f.readlines()
			diff = difflib.Differ().compare(new_file_content, old_lines)
			nb_diff = 0
			for d in diff:
				code = d[:2]
				if code in [ "+ ", "- "]:
					nb_diff += 1
			if nb_diff > diff_check_conf["max_diff"]:
				msg = MIMEText("A cause d'un trop grand nombre de modifications dans la génération de la table %s, cette table n'a pas été regénérée. Pour la regénérer, réexécuter le script de génération de table en modifiant le paramètre generate_if_diff.") # TODO regarder qu'on apelle pas le script toutes les minutes en crontab
				msg['Subject'] = "Trop de modification dans la génération de table Postfix"
				msg['From'] = "root@localhost"
				msg['To'] = ",".join(diff_check_conf["recipient"])
				
				s = smtplib.SMTP('localhost')
				s.send_message(msg)
				s.quit() # TODO test
				return True
		return False


class WriterStrategy(CheckStrategy):
	def handle_file(self, new_file_content, generator):
		generator.write_file(new_file_content)