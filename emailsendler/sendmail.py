import smtplib, ssl, shutil, os
from jinja2 import Environment, FileSystemLoader
from email.message import EmailMessage
from os import path
from zipfile import ZipFile
from shutil import make_archive
import pyminizip
from pathlib import Path

def get_archive(new_list_of_json, path_to_template, filename_template, path_to_archive):
    if not os.path.exists(path_to_archive):
        os.mkdir(path_to_archive)
    
    environment = Environment(loader=FileSystemLoader(path_to_template))
    template = environment.get_template(filename_template)

    for new_user in new_list_of_json:
        content = template.render(
            new_user
            )

        with open(f"{path_to_archive}/{new_user['id']}.txt", mode="w+", encoding="utf-8") as add_conf_file:
                add_conf_file.write(content)
                pyminizip.compress(add_conf_file.name, None, f'{path_to_archive}/{Path(add_conf_file.name).stem}.zip', "passwd",5)
                os.remove(add_conf_file.name)
        
