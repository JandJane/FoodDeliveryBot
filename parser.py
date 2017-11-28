# -*- coding: utf-8 -*-

import lxml.html as html
import urllib
import pandas as pd



def find_links(url):
    content = urllib.request.urlopen(url).read()
    doc = html.fromstring(content)
    doc.make_links_absolute(url)
    links = []
    menu = doc.get_element_by_id('aside')
    for link in menu.iterlinks():
        links.append(link[2])
    return links  


def parse_page(url, i):
    content = urllib.request.urlopen(url).read()
    doc = html.fromstring(content)
    doc.make_links_absolute(url)
    temp = doc.find_class('span3')[1].find_class('inner')
    if not len(temp):
        return
    else:
        new = []
        section = doc.find_class('span3')[1].find_class('inner')[i].text_content()
        section = ' '.join(section.split())
        for dish in doc.find_class('caption'):
            name = dish.find_class('name')
            if len(name):
                name = name[0].text_content().split()
                name = ' '.join(name).encode('utf8')
                price = int(dish.find_class('price_block')[0].text_content().split()[0][:-3])
                new.append([section, name, int(price)])
        return new


url = 'http://dushes-cafe.ru/menyu'
menu = pd.DataFrame(columns = ['section', 'dish', 'price'])
links = find_links(url)
for i in range(len(links)):
    d = parse_page(links[i], i)
    menu = menu.append(pd.DataFrame(d, columns = menu.columns), ignore_index = True)
menu.to_csv('menu.csv')