#!/usr/bin/python
import getopt, sys, os
from datetime import date, datetime
from collections import defaultdict
import ccl
from ccl import *


def usage():
    print \
        '''%s --csv <registration csv> [--after <date, e.g. 2015-09-20>] [--fill <output>] [--post <file>] [--summary <file>] [--sign <signup pdf>] <pod arrangement>
        --csv,   the csv file download from student registration sheet
        --fill,  fill the open duty, write to output file
        --after, fill open duties and display duty summary after this date, default is today()
        --post,  write to this file the POD information sorted by student's lastname
        --summary, write to this file the POD summary sorted by date
        --sign, write to a pdf file for POD signatures''' % sys.argv[0]
        
def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hf:a:p:s:x', 
                ['csv=', 'help', 'fill=', 'after=', 'post=', 'summary=', 'sign='])
    except getopt.GetoptError as err:
        print str(err)
        usage()
        sys.exit(1)

    csvfile = None
    output = None
    after = date.today()
    post  = summary = sign = None

    for o, v in opts:
        if o in ('-h', '--help'):
            usage()
            sys.exit(0)
        elif o == '--csv':
            csvfile = v
        elif o in ('-f', '--fill'):
            output = v
        elif o in ('-a', '--after'):
            y, m, d = v.split('-')
            after = date(int(y), int(m), int(d))
        elif o in ('-p', '--post'):
            post = v
        elif o in ('-s', '--summary'):
            summary = v
        elif o in ('-x', '--sign'):
            sign = v
            
    if csvfile is None :
        print >> sys.stderr, 'Missing student registration csv'
        usage()
        sys.exit(1)

    if not args:
        print >> sys.stderr, 'Missing constraint file'
        usage()
        sys.exit(1)

    cstfile = args[0]

    ccl.init(csvfile)
    asgm = Arrangement()
    asgm.load(cstfile)

    if output is not None:
        if not asgm.fill_duties(after):
            print >> sys.stderr, 'There is something wrong in filling duty spot, please adjust parameter and retry'
            sys.exit(1)
        with open(output, 'wt') as f:
            print >> f, str(asgm)
#        print asgm

    if post:
        with open(post, 'wt') as f:
            write_post(f, asgm)

    if summary:
        with open(summary, 'wt') as f:
            write_summary(f, asgm, after)
   
    if sign:
        write_pdf_pod_signature(sign, asgm, after)
            
def write_post(fh, asgm):
    ps = defaultdict(list)
    for duty in asgm.duties:
        for s in duty.students:
            ps[s.parent].append( (s, duty.date, duty.name) )
    
    sep = '-'*40
    for ss in sorted(ps.values(), key = lambda ss: ss[0][0].lastname):
        print >> fh, sep
        for student, date, dname in ss:
            print >> fh, '%s, %s (%s) \t %s [%s]' % (student.lastname, student.firstname, student.cls, date, dname)

    print >> fh, sep
        

def write_summary(fh, asgm, after):
    all = defaultdict(list)
    for duty in asgm.duties:
        if duty.date <= after: continue
        all[duty.date].append(duty)
 
    for dt in sorted(all):
        ds = all[dt]
        print >> fh, '----- %s ------' % dt.strftime('%B %d, %Y')
        for d in ds:
            leading = '[%s]'%d.name
            for s in d.students:
                print >> fh, '[%s]  %s \t%s %s' % (d.name, s, s.parent.phones_str, s.parent.emails_str)
            print >> fh

def write_pdf_pod_signature(pdff, asgm, after):
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch, pica

    styles = getSampleStyleSheet()
    
    doc = SimpleDocTemplate(pdff, pagesize=letter, bottomMargin=0.5*inch)
    elements = []
    
    ts = TableStyle([('SPAN',(2,0),(3,0)),
                        ('GRID', (0,0), (-1,-1), 0.25, colors.black),
                        ('LINEBELOW',(0,0),(-1,0),1,colors.black),
                        ('BOX', (0,0), (-1,-1), 0.5, colors.black),
                        ('FONT', (0,0), (-1,-1), 'Helvetica-Bold',16),
                        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                    ])
    
    all = defaultdict(list)
    for duty in asgm.duties:
        if duty.date <= after: continue
        all[duty.date].append(duty)
 
    for dt in sorted(all):
        elements.append(Paragraph(dt.strftime('%B %d, %Y'), styles["Heading2"]))
        elements.append(Paragraph('SBCCL Parent-on-Duty Sign In/Out Sheet', styles["Heading1"]))
        elements.append(Spacer(1,0.4*inch))
        ds = all[dt]
        for d in ds:
            leading = '[%s]'%d.name
            data= [(d.name, 'Board Member  ', ' '*40, '') ]
            
            for s in d.students:
                data.append((d.name, s, '', ''))
            t=Table(data, rowHeights=(2.9*pica,)*len(data), hAlign='LEFT')
            t.setStyle(ts)
            elements.append(t)
            elements.append(Spacer(1, 0.8*inch))
        elements.append(PageBreak())
        
    doc.build(elements)
    
if __name__ == "__main__":
    main()
    
    

