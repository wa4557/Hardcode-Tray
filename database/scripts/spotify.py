#!/usr/bin/python3
from imp import load_source
from os import makedirs, path, remove
from shutil import make_archive, move, rmtree
from subprocess import PIPE, Popen
from sys import argv
from zipfile import ZipFile

absolute_path = path.split(path.abspath(__file__))[0] + "/"
svgtopng = load_source('svgtopng', absolute_path + 'svgtopng.py')
spotify_path = "/tmp/_spotify/"
icons_path = "%s_linux/" % spotify_path

zip_file = argv[3] + argv[4]
original_icon = argv[2]
theme_icon = argv[1]
step = int(argv[5])
icon_size = int(path.splitext(original_icon)[0].split("-")[-1])

if svgtopng.is_svg_enabled():
    if step == 0:
        if path.exists(spotify_path):
            rmtree(spotify_path)
        makedirs(spotify_path, exist_ok=True)
        p = Popen(["chmod", "0777", spotify_path], stdout=PIPE, stderr=PIPE)
        p.communicate()
        with ZipFile(zip_file) as zf:
            zf.extractall(spotify_path)

    svgtopng.convert_svg2png(theme_icon, icons_path + original_icon, icon_size)

    if step == -1:
        if path.isfile(zip_file):
            remove(zip_file)

        make_archive(zip_file.replace(".zip", ""), 'zip', spotify_path)
        rmtree(spotify_path)
