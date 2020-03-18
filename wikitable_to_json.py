import requests
import json
import re
import os
from bs4 import BeautifulSoup

def tableToJson(table):
    rows = table.tbody.findChildren('tr')

    headerRow = rows[0]
    headings = []
    for td in headerRow.stripped_strings:
        headings.append(td)
    rows.pop(0)

    numItems = len(rows)
    items = []
    for ind in range(numItems):
        items.append({})
    for ind in range(numItems):
        cols = rows[ind].findChildren('td')
        for heading in headings:
            if(items[ind].get(heading) == None):
                if (len(cols) > 0):
                    col = cols.pop(0)
                    val = ' '.join(col.stripped_strings).strip()
                    if(col.get('rowspan') == None):
                        rowspan = 1
                    else:
                        rowspan = int(col.get('rowspan'))
                    for i in range(rowspan):
                        if ind + i < numItems:
                            items[ind + i][heading] = val
    return items

def removeEmptyValues(items):
    for item in items:
        emptyKeys = []
        for key in item:
            if item[key] == '':
                emptyKeys.append(key)
        for key in emptyKeys:
            del item[key]

wikipage = input("Enter a wikipedia page url: ")
response = requests.get(wikipage)
soup = BeautifulSoup(response.text, "html.parser")
body = soup.body
title = soup.find(id="firstHeading").string.strip()
if not os.path.exists(title):
    os.mkdir(title)

while(True):
    tableName = input("Enter a table name (-1 to quit): ")
    if(tableName == '-1'):
        break
    else:
        strings = body.findAll(text=tableName)
    if len(strings) == 0:
        print("No such table exists in " + wikipage)
    else:
        for string in strings:
            # string.parent is a span element, its parent is a heading element
            heading = string.parent.parent
            if (re.match('h[1-6]|p', heading.name)):
                table = heading.next_sibling
                # sometimes '\n' can be the next sibling of heading element
                while table.name != 'table':
                    table = table.next_sibling
                items = tableToJson(table)
                removeEmptyValues(items)
                with open(title + '/' + tableName + '.json', 'w') as f:
                    json.dump(items, f, indent=4, sort_keys=True)