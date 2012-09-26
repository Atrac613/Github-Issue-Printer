#!/usr/bin/env python
#
# Copyright (C) 2012 atrac613.io.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

__author__ = 'me@atrac613.io (Osamu Noguchi)'

import os
import datetime
import sqlite3
from threading import Timer

import wrap
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas
from github3 import client

from config import GITHUB_SETTINGS
from config import PRINT_COMMAND
from config import DB_FILE_NAME
from config import FONT
from config import FONT_NAME

class GHIssuePrinter():
    def init_db(self):
        self.debug('Init', 'Database Initializing.')

        if not (os.path.isfile(DB_FILE_NAME)):
            db=sqlite3.connect(DB_FILE_NAME)
            db.execute('create table issue_id(\
                        id integer PRIMARY KEY AUTOINCREMENT,\
                        user,\
                        repo,\
                        issue_id)')
        
            for key, value in GITHUB_SETTINGS.items():
                c = client.Client(username=value['account'],
                                password=value['password'])

                for _key, _value in value['repos'].items():
                    for _repo in _value:
                        repo = client.Repo(c, _key, _repo)
                        issues = repo.issues()

                        count = 0
                        for issue in issues:
                            #db.execute('insert into issue_id(\
                            #            user,\
                            #            repo,\
                            #            issue_id) values (?, ?, ?)',
                            #            [_key,
                            #            _repo,
                            #            (str(issue['number']))])
                            count = count + 1

                        db.commit()
 
                        self.debug('Init',
                                   '%s/%s : Add %d issues.' % (_key,
                                   _repo, count))
        
            db.close()

    def check_issue(self):
        self.debug('Check', 'Checking Issue.')

        db=sqlite3.connect(DB_FILE_NAME)
        cur = db.cursor()
    
        for key, value in GITHUB_SETTINGS.items():
            self.debug('Check', key + ': Checking.')
            c = client.Client(username=value['account'],
                            password=value['password'])

            for _key, _value in value['repos'].items():
                for _repo in _value:
                    repo = client.Repo(c, _key, _repo)
                    issues = repo.issues()

                    for issue in issues:
                        cur.execute("select issue_id from issue_id where\
                                    user = ? and\
                                    repo = ? and\
                                    issue_id = ?",\
                                    [_key,
                                    _repo,
                                    (str(issue['number']))])

                        if len(cur.fetchall()) == 0:
                            self.debug('Check',
                               '%s/%s: Find Issue #%d' % (_key,
                               _repo, issue['number']))

                            self.create_pdf(_key, _repo, issue)
                            self.print_pdf(_key, _repo, issue['number'])

                            #db.execute('insert into issue_id(\
                            #            user,\
                            #            repo,\
                            #            issue_id) values (?, ?, ?)',
                            #            [_key,
                            #            _repo,
                            #            (str(issue['number']))])

                            db.commit()

        cur.close()
        db.close()

    def create_pdf(self, user, repo, issue):
        self.debug('Create', 'Creating PDF.')

        os.chdir('pdf')
    
        if not (os.path.isdir(user)):
            os.mkdir(user)
        
        os.chdir(user)

        if not (os.path.isdir(repo)):
            os.mkdir(repo)

        os.chdir(repo)
    
        issue_id = issue['number']
        filename = '%d.pdf' % issue_id
    
        self.debug('Create', 'Creating %s/%s/%s' % (user, repo, filename))
        
        title = issue['title']
        body = issue['body']
        name = issue['user']['login']
        number = issue['number']
        url = issue['html_url']
        avator_url = issue['user']['avatar_url']
        created_at = issue['created_at']

        td = datetime.timedelta(hours=9)
        created_at = datetime.datetime.strptime(created_at,
                                                '%Y-%m-%dT%H:%M:%SZ') + td

        if body == '':
            os.chdir('..%s..%s..' % (os.sep, os.sep))

            return

        body = 'Date : %s\n\n%s' % (created_at, body)

        wrap_body = wrap.wrap(body, 39)
        wrap_title = wrap.wrap(title, 39)

        row =  wrap_body.count('\n') + wrap_title.count('\n')
        height = 350 + row * 12

        c = canvas.Canvas(filename, pagesize=(220, height))
        pdfmetrics.registerFont(FONT)

        c.drawImage('..%s..%slogo.png' % (os.sep, os.sep),
                    60, height-110,
                    100, 100,
                    mask='auto', preserveAspectRatio=True)

        c.drawImage(avator_url.encode('UTF-8'),
                    10, height-195,
                    50, 50,
                    mask='auto', preserveAspectRatio=True)

        c.setFont(FONT_NAME, 10)
        t = c.beginText(10, height-110)
        t.textLines('Account: %s' % user)
        c.drawText(t)

        t = c.beginText(10, height-125)
        t.textLines('Project: %s' % repo)
        c.drawText(t)

        c.line(10, height - 135, 210, height - 135)

        c.setFont(FONT_NAME, 15)
        t = c.beginText(70, height-188)
        t.textLines(name)
        c.drawText(t)

        c.setFont(FONT_NAME, 20)
        t = c.beginText(70, height-168)
        t.textLines('Issue #%s' % number)
        c.drawText(t)

        c.line(10, height - 205, 210, height - 205)

        c.setFont(FONT_NAME, 10)

        t = c.beginText(10, height-225)
        t.textLines(wrap_title)
        c.drawText(t)

        _height = wrap_title.count('\n') * 12 + 225
        c.line(10, height - _height, 210, height - _height)

        t = c.beginText(10, height - _height - 20)
        t.textLines(wrap_body.encode('utf-8'))
        c.drawText(t)

        qr_url = 'http://chart.apis.google.com/chart?chs=150x150&cht=qr&chl=%s' % url
        c.drawImage(qr_url.encode('UTF-8'),
                    60, 10,
                    100, 100,
                    mask='auto', preserveAspectRatio=True)

        c.showPage()
        c.save()

        os.chdir('..%s..%s..' % (os.sep, os.sep))

    def print_pdf(self, user, repo, issue_id):
        self.debug('Print', 'Printing PDF.')

        os.chdir('pdf')
        os.chdir(user)
        os.chdir(repo)

        filename = '%d.pdf' % issue_id
    
        self.debug('Print', 'Printing %s/%s/%s' % (user, repo, filename))
    
        #if (os.path.isfile(filename)):
            #os.system(PRINT_COMMAND % filename)
        
        os.chdir('..%s..%s..' % (os.sep, os.sep))

    def debug(self, section, log):
        date = datetime.datetime.today()
        print '[%s - %s] %s' % (date.strftime('%Y-%m-%d %H:%M:%S'),
                                section, log)

