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
		if not os.path.isfile(generator.map_conf()["file"]):
			# the file doesn't exist, there is no diff to check
			return False

		diff_check_conf = generator.diff_checks()
		if (not diff_check_conf) or diff_check_conf["generate_if_diff"]:
			# even when there is too much diff we generate the file, so there is no need to check
			return False

		with open(generator.map_conf()["file"]) as f:
			old_lines = f.readlines()
			diff = difflib.Differ().compare(new_file_content, old_lines)
			nb_diff = 0
			for d in diff:
				code = d[:2]
				if code in [ "+ ", "- "]:
					nb_diff += 1
			if nb_diff > diff_check_conf["max_diff"]:
				opt_list = generator.opt_list()
				force = ("-f", "") in opt_list
				if force:
					print("Trop de changement dans la table %s, cette table sera tout de même générée." % generator.map_conf()["file"])
					return False
				else:
					msg = MIMEText("A cause d'un trop grand nombre de modifications dans la génération de la table %s, cette table n'a pas été regénérée. Pour la regénérer, réexécutez le script de génération de table en modifiant le paramètre generate_if_diff." % generator.map_conf()["file"])
					msg['Subject'] = "Trop de modification dans la génération de table Postfix"
					msg['From'] = diff_check_conf["sender"]
					msg['To'] = ",".join(diff_check_conf["recipient"])
				
					s = smtplib.SMTP(diff_check_conf["smtp_server"])
					s.send_message(msg)
					s.quit()

					print("The file %s has NOT been generated due to too much change, to generate it anyway use the flag -f" % generator.map_conf()["file"])
					return True
		return False
