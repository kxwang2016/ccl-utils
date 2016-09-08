#!/usr/bin/python
import getopt, sys
import ccl
from ccl import *
from collections import defaultdict

def usage():
    print '%s --class <classname, eg. B1P> --csv <csv of student registration sheet>' % sys.argv[0]

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

    
    bucket = defaultdict(list)    
    students = []
    ccl.init(csvfile)
    for cls in [Class.get(cname) for cname in classname.split(',')]:
        if not cls:
            print >> sys.stderr, 'Unknow classname %s'%classname
            sys.exit(1)
        students += filter(lambda s: s.isActive(), cls.students)

    print '######## %s ########'%classname
    total_amt = 0
    total_students = 0
    for s in students:
        check = s.tuition_check
        total_amt += check.amt
        total_students += 1
        bucket[check.amt].append(s)

    for amt in sorted(bucket):
        ss = bucket[amt]
        print '$%d [%d]'%(amt, len(ss))
        for s in ss:
            check = s.tuition_check
            print '\t%12s  #%4s  %s' % (check.status, check.no, repr(s))
        print

    print 'Total Amount = $%d' % total_amt
    print 'Total Student = %d' % total_students
    print

if __name__ == "__main__":
    main()
    
    

