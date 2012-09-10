# -*- coding: utf-8 -*-

import os
import datetime
import sqlite3
from threading import Timer

import wrap
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from github3 import client

from config import GITHUB_SETTINGS
from config import PRINTER_NAME
from config import DB_FILE_NAME

def initDB():
    printLOG('DB', 'Database Initializing.')

    if not (os.path.isfile(DB_FILE_NAME)):
        db=sqlite3.connect(DB_FILE_NAME)
        db.execute('create table issue_id(id integer PRIMARY KEY AUTOINCREMENT, user, issue_id)')
        
        for key, value in GITHUB_SETTINGS.items():
            c = client.Client(username=value['account'], password=value['password'])
            for _key, _value in value['repos'].items():
                for _repo in _value:
                    repo = client.Repo(c, _key, _repo)
                    issues = repo.issues()

                    count = 0
                    for issue in issues:
                        #db.execute('insert into issue_id(user, issue_id) values (?, ?)', [value['account'], (str(issue['number']))])
                        count = count + 1

                    db.commit()
 
                    printLOG('DB', '%s : Add %d issues.' % (_repo, count))
        
        db.close()

def checkIssues():
    printLOG('Issue', 'Checking Issue.')

    db=sqlite3.connect(DB_FILE_NAME)
    cur = db.cursor()
    
    for key, value in GITHUB_SETTINGS.items():
        printLOG('Issue', key + ': Checking.')
        c = client.Client(username=value['account'], password=value['password'])
        for _key, _value in value['repos'].items():
            for repo in _value:
                repo = client.Repo(c, _key, repo)
                issues = repo.issues()

                for issue in issues:
                   cur.execute("select issue_id from issue_id where user = ? and issue_id = ?", [value['account'], (str(issue['number']))])
                   if len(cur.fetchall()) == 0:
                       createPDF(key, issue)
                       printPDF(key, issue['number'])

                       #db.execute('insert into issue_id(user, issue_id) values (?, ?)', [value['account'], (str(issue['number']))])

                       printLOG('DB', '%s: Insert ID %d' % (key, issue['number']))

                       db.commit()

    cur.close()
    db.close()

def createPDF(user, issue):
    printLOG('PDF', 'Creating PDF.')
    os.chdir('pdf')
    
    if not (os.path.isdir(user)):
        os.mkdir(user)
        
    os.chdir(user)
    
    issue_id = issue['number']
    filename = '%d.pdf' % issue_id
    
    printLOG('PDF', 'Creating %s' % filename)

    title = issue['title']
    body = issue['body']
    name = issue['user']['login']
    number = issue['number']
    url = issue['html_url']
    avator_url = issue['user']['avatar_url']

    if body == '':
        return

    wrap_body = wrap.wrap(body, 39)
    wrap_title = wrap.wrap(title, 39)

    row =  wrap_body.count('\n') + wrap_title.count('\n')
    height = 290 + row * 12

    c = canvas.Canvas(filename, pagesize=(220, height))
    msgothic = UnicodeCIDFont("HeiseiKakuGo-W5")
    pdfmetrics.registerFont(msgothic)

    c.drawImage('..' + os.sep + 'logo.png', 60, height-100, 100, 100, mask='auto', preserveAspectRatio=True)
    c.drawImage(avator_url.encode('UTF-8'), 10, height-135, 50, 50, mask='auto', preserveAspectRatio=True)

    c.setFont('HeiseiKakuGo-W5', 15)
    t = c.beginText(70, height-130)
    t.textLines(name)
    c.drawText(t)

    c.setFont('HeiseiKakuGo-W5', 20)
    t = c.beginText(70, height-110)
    t.textLines('Issue #%s' % number)
    c.drawText(t)

    c.line(10, height - 145, 210, height - 145)

    c.setFont('HeiseiKakuGo-W5', 10)

    t = c.beginText(10, height-165)
    t.textLines(wrap_title)
    c.drawText(t)

    _height = wrap_title.count('\n') * 12 + 165
    c.line(10, height - _height, 210, height - _height)

    t = c.beginText(10, height - _height - 20)
    t.textLines(wrap_body.encode('utf-8'))
    c.drawText(t)

    qr_url = 'http://chart.apis.google.com/chart?chs=150x150&cht=qr&chl=%s' % url
    c.drawImage(qr_url.encode('UTF-8'), 60, 10, 100, 100, mask='auto', preserveAspectRatio=True)

    c.showPage()
    c.save()

    os.chdir('..' + os.sep + '..')

def printPDF(user, issue_id):
    printLOG('PRINT', 'Printing PDF')

    os.chdir('pdf')
    os.chdir(user)
    filename = '%d.pdf' % issue_id
    
    printLOG('PRINT', 'Printing %s' % filename)
    
    #if (os.path.isfile(filename)):
        #os.system(GSPRINT_COMMAND + ' -printer ' + PRINTER_NAME + ' ' + filename)
        
    os.chdir('..' + os.sep + '..')

def printLOG(section, log):
    date = datetime.datetime.today()
    print '[' + date.strftime('%Y-%m-%d %H:%M:%S') + ' - ' + section + '] ' + log

if __name__ == "__main__":
    printLOG('SYSTEM', 'Starting Github Issue Printer.')
    
    initDB()
    
    checkIssues()
    
    sec = 180.0
    
    printLOG('SYSTEM', 'Timer Setting. (%d sec)' % sec)
    
    while True:
        t = Timer(sec, checkIssues)
        t.run()
