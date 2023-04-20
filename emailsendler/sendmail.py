import smtplib, ssl, shutil, os, sys, configparser
from jinja2 import Environment, FileSystemLoader
from email.message import EmailMessage
from os import path
from zipfile import ZipFile
from shutil import make_archive
import pyminizip
from pathlib import Path                                  
from email import encoders                                  # Импортируем энкодер
from email.mime.base import MIMEBase                        # Общий тип
from email.mime.text import MIMEText                        # Текст/HTML
from email.mime.image import MIMEImage                      # Изображения
from email.mime.audio import MIMEAudio                      # Аудио
from email.mime.multipart import MIMEMultipart              # Многокомпонентный объект

def send_mail_message(new_list_of_json):

    config = configparser.ConfigParser()
    config.read('mail.ini')

    mail_conf = config['email']
    addr_from = mail_conf['SmtpLogin']
    passwd = mail_conf['SmtpPassword']
    smtp_server = mail_conf['SmtpServer']
    smtp_port = int(mail_conf['SmtpPort'])

    title_mail = 'Диагрупп ВПН'
    body_text = 'Зравствуйте! \nПароль от архива ваш номер телефона!!!'
    body_mail = MIMEText(body_text, 'plain')
    path_to_template = "./templates"
    file_name_zip_template = "zip_template.txt"
    path_to_archive = './client_archives'
    
    if not os.path.exists(path_to_archive):
        os.mkdir(path_to_archive)
    
    environment = Environment(loader=FileSystemLoader(path_to_template))
    template = environment.get_template(file_name_zip_template)

    context=ssl.create_default_context()


    smtp = smtplib.SMTP(smtp_server, smtp_port)
    smtp.starttls(context=context)
    smtp.login(addr_from, passwd)

    for row in new_list_of_json:
        attachment = MIMEBase('application', "octet-stream")
        msg = MIMEMultipart()
        msg["Subject"] = title_mail
        msg["From"] = addr_from
        msg["To"] = row['email']

        content = template.render(row)

        try:
            with open(f"{path_to_archive}/{row['id']}.json", mode="w+", encoding="utf-8") as add_conf_file:
                add_conf_file.write(content)
                file_to_attach = f'{path_to_archive}/{Path(add_conf_file.name).stem}.zip'
            add_conf_file.close()

            pyminizip.compress(add_conf_file.name, None, file_to_attach, f'{row["number"]}', 0)
            os.remove(add_conf_file.name)

            filename_to_attach = os.path.basename(file_to_attach)
            attachment.set_payload(content)
            encoders.encode_base64(attachment)
            attachment.add_header('Content-Disposition', 'attachment', filename=filename_to_attach)
            msg.attach(body_mail)
            msg.attach(attachment)

        except IOError:
            msg = "Error opening attachment file %s" % file_to_attach
            print(msg)
            sys.exit(1)

        try:
            smtp.send_message(msg)
            print(f'Сообщение отправлено по адресу: {row["email"]}')
        except Exception as err:
            print(f'Сообщение не доставлено адресату: {row["email"]}')
            print("Error: unable to send email: %s" % err)
            continue
    
    smtp.quit()
