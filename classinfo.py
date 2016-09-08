#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import getopt, sys, codecs
import ccl
from ccl import *

def usage():
    print '%s --class <language|culture|classname, eg. B1P, Dance> --csv <csv of student registration sheet>' % sys.argv[0]

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'h', ['class=', 'csv=', 'help'])
    except getopt.GetoptError as err:
        print str(err)
        usage()
        sys.exit(1)

    csvfile, classname = None, None
    for o, v in opts:
        if o in ['-h', '--help']:
            usage()
            sys.exit(0)
        elif o == '--class':
            classname = v
        elif o == '--csv':
            csvfile = v

    if not sys.stdout.isatty():
        sys.stdout = codecs.getwriter('utf8')(sys.stdout)
        
    ccl.init(csvfile)
    classes = []
    # collect classes of interest
    if classname.lower() == "language":
        classes = [cls for cls in Class.all() if cls.isLanguageClass()]
    elif classname.lower() == "culture":
        classes = [cls for cls in Class.all() if cls.isCultureClass()]
    else:
        classes = []
        for clsnm in classname.split(','):
            cls = Class.get(clsnm.strip())
            if not cls:
                cls = Class.get(clsnm.lower().strip())
                if not cls:
                    print >> sys.stderr, 'Unknow classname %s'%clsnm
                    sys.exit(1)
            classes.append(cls)

    # output contact info class by class
    header =   '%s * %-25s * %-32s * %-30s' % (u'学生中文名', u'学生英文名', u'电话', "email")
    fmt    = '%s   * %-30s * %-34s * %-30s'
    for cls in classes:
        email_list = set()
        roster = []
        for s in cls.students:
            if not s.isActive(): continue
            email_list |= s.parent.emails
            roster.append( fmt % (s.cname, s.name, s.parent.phones_str, s.parent.emails_str) )

        if roster:
            print '--- CLASS %s ---'%cls.name
            print header
            print '\n'.join(roster)
            print '\nAll email: ' + ','.join(list(email_list))
            print '\n'
    
if __name__ == "__main__":
    main()
    
    

