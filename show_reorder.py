#! /user/bin/python3

import re
from os.path import isfile, join
from os import listdir, rename
from urllib import request

mypath = './'
show_id = "73871"
dvd_order = request.urlopen('https://www.thetvdb.com/index.php?id=' + show_id + '&tab=seasonall&order=dvd')
air_order = request.urlopen('https://www.thetvdb.com/index.php?id=' + show_id + '&tab=seasonall&order=aired')
dvd_order = re.findall(r"(?:<tr>)(?:.*)(?:lid=7\">)(\d+ x \d+)(?:.*)(?:lid=7\">)(.*)(?=</a>)", dvd_order.read().decode('utf-8'))
air_order = re.findall(r"(?:<tr>)(?:.*)(?:lid=7\">)(\d+ x \d+)(?:.*)(?:lid=7\">)(.*)(?=</a>)", air_order.read().decode('utf-8'))
files = [f for f in listdir(mypath) if isfile(join(mypath, f))]
renamed_files = {}
sanitize_char = "([\"',:&])|(\.\.)"
order_graph = {"title": {}, "air": {}, "dvd": {}}

# Remove unwanted characters from string.
def sanitize(string):
    temp = string.replace(" ", '.').replace(",","")\
                                   .replace("\"", "").replace("\'", "")\
                                   .replace("&", "and").replace(":", "")\
                                   .replace('..', '.').replace("%", ".Percent")\
                                   .replace("!", "")
    return temp

# Check episode format for single digit numbers and pad with zero.
def double_check(match_obj):
    return 'S' + match_obj.group(1).zfill(2) + 'E' + match_obj.group(2).zfill(2)

# Reformat episode list to S<n>E<n> format for episode numbers,
# and the title with word dot format.
def html_parse(order):
    for i, item in enumerate(order):
        episode_re = re.sub(r"(\d+)(?: x )(\d+)", double_check, item[0])
        title_san = sanitize(item[1])
        item = (episode_re, title_san)
        order[i] = item

    return order

# Create graph of air_order and dvd_order relationships.
def create_graph(air_order, dvd_order):
    for air in air_order:
        for dvd in dvd_order:
            if air[1] == dvd[1]:
                order_graph["title"][air[1]] = (air[0], dvd[0])
                order_graph["air"][air[0]] = (dvd[0], dvd[1])
                order_graph["dvd"][dvd[0]] = (air[0], air[1])
                break

# Compare file name to episode title. Matches are saved to dictionary with file
# name as the key.
def match(air_order, dvd_order):
    for i in files:
        i_san = sanitize(i)
        for dvd in dvd_order:
            regex = re.search(dvd[1], i_san, re.I)
            if regex:
                temp = re.sub(r'S\d+E\d+', dvd[0], i)
                renamed_files[i] = temp
                dvd_order.remove(dvd)
                break
        for air in air_order:
            if i not in renamed_files:
                regex = re.search(air[0], i_san, re.I)
                if regex:
                    new_episode_id = order_graph[air[0]][0]
                    new_title = order_graph[air[0]][1]
                    end_string = re.search(r"(DVDRip|1080p).*", i_san, re.I)
                    temp = re.sub(r"(S\d+E\d+\.).*", new_episode_id + "." +
                                  new_title + "." + end_string.group(0), i_san)
                    renamed_files[i] = temp
                    air_order.remove(air)
                    break

# Rename files
def file_rename():
    for i in files:
        try:
            rename(i, renamed_files[i])
        except KeyError:
            print('Match not found: ' + i)
            continue

air_order = html_parse(air_order)
dvd_order = html_parse(dvd_order)
create_graph(air_order, dvd_order)
match(air_order, dvd_order)
file_rename()
