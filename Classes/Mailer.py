from email.mime.text import MIMEText
import smtplib
import os

# forward declaration
class Mailer:
	pass


class MailingStrategy:
	def __init__(self, from_who: str, to: str, title: str, message: str, smtp_server: str) -> None:
		self._from = from_who
		self._to = to
		self._title = title
		self._message = message
		self._smtp = smtp_server

	def send_message(self) -> bool:
		return False


class Mailer:
	_instance = None
	
	def __init__(self) -> None:
		self._mailing_strategies = []

	def add_mailing_strategy(self, strat: MailingStrategy) -> None:
		if not strat in self._mailing_strategies:
			self._mailing_strategies.append(strat)

	@classmethod
	def get_instance(cls) -> Mailer:
		if not cls._instance:
			cls.create()
		return cls._instance

	@classmethod
	def create(cls) -> None:
		if not cls._instance:
			cls._instance = Mailer()

	@classmethod
	def register_strat(cls, filt: MailingStrategy) -> Mailer:
		instance = cls.get_instance()
		instance.add_mailing_strategy(filt)
		return cls

	def send_mail(self, from_who: str, to: str, title: str, message: str, smtp_server: str) -> bool:
		for strat_class in self._mailing_strategies:
			strat = strat_class(from_who, to, title, message, smtp_server)
			if strat.send_message():
				return True
		return False


@Mailer.register_strat
class SmtpLibStrat(MailingStrategy):
	def send_mesage(self) -> bool:
		msg = MIMEText(self._message)
		msg['Subject'] = self._title
		msg['From'] = self._from
		msg['To'] = ",".join(self._to)
				
		s = smtplib.SMTP(self._smtp_server)
		try:
			s.send_message(msg)
			s.quit()
		except smtplib.SMTPException:
			print("Error while sending mail with smtplib")
			s.quit()
			return False

		return True


@Mailer.register_strat
class CLIMailingStrat(MailingStrategy):
	"""
	if sendmail is not working try with mail even if we cannot specify from and smtp server at least the mail might be sent
	This strat should alwas be the last one to use
	"""
	def send_message(self)-> bool:
		mail_cmd = "echo \"" + self._message + "\" | mail -s \"" + self._title + "\" " + " ".join(self._to)
		ret = os.system(mail_cmd)
		if ret != 0:
			print("Error while sending mail with mail in CLI")
		return ret == 0


