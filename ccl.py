# -*- coding: utf-8 -*-
# must run in a command window
# this version temporarily assign an 0 id to inactive students
import sys, re, csv, re, random, math
from datetime import date
from collections import OrderedDict, namedtuple

def _proc_name(name):
    '''formalize name string, for example " Josh  Huang " ==> "Josh Huang"'''
    return re.sub(r'\s+', ' ', name.strip())

def _proc_phone(number):
    '''formalize phone numbers'''
    return number.strip()

def _proc_email(email):
    '''formalize email string'''
    email.replace("mailto:", "")
    return email.strip()

# The following dictionaries can be considered as
# Tables in CCL database
_students = {}
_parents  = {}
_classes  = {}

def __ensure_init():
    if not __students or not __parents or not __classes:
        raise Exception('CCL database not initialized')

class Parent:
    def __init__(self, mom="", dad=""):
        self.mom = _proc_name(mom)
        self.dad = _proc_name(dad)
        if not self.mom and not self.dad:
            raise Exception('No Mom and Dad name')
        self.key = (self.mom, self.dad)
        self.phones = set()
        self.emails = set()
        self.children = set()

    def add_child(self, child):
        self.children.add(child)
        child.parent = self
    
    def add_phone(self, phone):
        phone = _proc_phone(phone);
        if not phone: return
        self.phones.add(phone)

    def add_email(self, email):
        email = _proc_email(email);
        if not email: return
        self.emails.add(email)

    def __repr__(self):
        return '{%s, %s, #children=%d}' % (self.mom, self.dad, len(self.children))

    @property
    def emails_str(self):
        return ','.join(list(self.emails))

    @property
    def phones_str(self):
        return ','.join(list(self.phones))

    @classmethod
    def all(cls): 
        return _parents.values()
    
    @classmethod
    def get(cls, key):  # by id
        return _parents[key]

    @classmethod
    def find(cls, name):
        ps = [p for p in Parent.all() if p.dad == name or p.mom == name]
        if len(ps)>1:
            raise Exception('There are more than one parent named "'+name+'"')
        elif len(ps)==1:
            return ps[0]
        else:
            return None

    @classmethod
    def add(cls, parent):
        if parent.key in _parents:
            parent = _parents[parent.key]
        else:
            _parents[parent.key] = parent
        return parent

class Check:
    def __init__(self, amt, no, status):
        if not amt:
            self.amt = 0
        else:
            self.amt = int(amt)
        self.no  = no
        self.status = status

    def __str__(self):
        if not no: return 'NA'
        return '$%d (%s)'%(self.amt, self.status)

class Student:
    def __init__(self, id, chinesename, name, status, pod=False):
        # assign 3 Chinese full spaces for empty Chinese name
        if chinesename == "": chineseName = None
        self.chinesename = chinesename
        self.name = _proc_name(name)
        self.status = status
        self.pod    = pod
        self.id     = self.key = int(id)
        self.parent = None
        self.cls    = None
        self.culture = None
        self.tuition_check = self.pod_check = self.donation_check = None
    
    def __repr__(self):
        return '[ID=%3d, %s (%s)]' % (self.id, self.name, self.cls.name)

    def __str__(self):
        return '%s (%s)' % (self.name, self.cls.name)

    def register(self, cls, culture = None):
        self.cls = cls
        cls.students.add(self)
        if culture:
            self.culture = culture
            culture.students.add(self)

    def isActive(self):
        return self.status in ["Received", "Active", "Pending"]

    def isPending(self):
        return self.status in ["Pending"]

    @property  # return fixed width string 
    def cname(self):
        '''Return formatted chinese name'''
        name = self.chinesename
        if name is None: name = ""
        name = unicode(name, 'utf-8')
        return ('%-' + str(8-len(name)) + 's') % name

    @property
    def firstname(self):
        fn, _ = self.name.rsplit(' ', 1)
        return fn

    @property
    def lastname(self):
        _, ln = self.name.rsplit(' ', 1)
        return ln

    @classmethod
    def all(cls):
        '''return all student list'''
        return _students.values()

    @classmethod
    def get(cls, key):
        '''return a student by ID'''
        return _students[key]

    @classmethod
    def find(cls, name, classname=None):
        '''return student with specific name and classname, if given'''
        if classname:
            cls = Class.get(classname)
            for s in cls.students:
                if s.name == name: return s
        else:
            ss = [s for s in Student.all() if s.name == name]
            if len(ss)>1:
                raise Exception('There are more than one student named "'+name+'", please add classname to distinguish')
            elif len(ss)==1:
                return ss[0]
        return None

    @classmethod
    def add(cls, student):
        '''add a student to student table'''
        if student.key in _students:
            student = _students[student.key]
        else:
            _students[student.key] = student
        return student

class Class:
    _language_class_rep = re.compile(r'(K|C|B)(\d+)?(A|P)(\d+)?')  # regular expression to detection AM/PM class
    def __init__(self, name):
        self.name = self.key = name
        self.students = set()

    def __repr__(self): return self.name

    def isCultureClass(self):
        return not self.isLanguageClass()
            
    def isLanguageClass(self):
        m = Class._language_class_rep.match(self.name)
        if m or self.isAdultClass() or self.isAP():
            return True
        return False

    def isAdultClass(self): return self.name == "AA"

    def isBilingual(self):
        return self.isLanguageClass() and (self.name == "AA" or self.name[:1] == "C")

    def isAP(self):
        return self.name in ["Pre-AP", "AP"]

    def ampm(self):
        '''return NOON/AM/PM'''
        if self.isCultureClass(): return "NOON"
        if self.isAdultClass(): return "AM"
        if self.name == "Pre-AP": return "AM"   # this could change each year
        if self.name == "AP": return "AM"       # this could change each year

        m = Class._language_class_rep.match(self.name)
        if m:
            return m.group(3)+"M"
        else:
            raise Exception('Unrecognized class name "'+self.name+'"')
            
    def isMorningClass(self):
        return self.ampm() == "AM"

    def grade(self):
        if self.isCultureClass(): return None
        if self.name == "AA": return 100
        if self.name == "Pre-AP": return 9
        if self.name == "AP": return 10
        
        m = Class._language_class_rep.match(self.name)
        if m:
            if m.group(1) == "K": return 0
            return int(m.group(2))
        else:
            raise Exception('Unrecognized class name "'+self.name+'"')

    @classmethod
    def all(cls):
        return _classes.values()

    @classmethod
    def get(cls, key):
        return _classes[key]

    @classmethod
    def add(cls, o):
        if o.key in _classes:
            o = _classes[o.key]
        else:
            _classes[o.key] = o
        return o


def __init_registration(filename):
    '''read from csv file download from google spreadsheet, and initialize students/parents/classes tables'''
    headerNames = (
      ID,  SCHOOL_YEAR, CLASS, STUDENT_CHINESE_NAME, STUDENT, POD, 
      # FAMILY, FAMILY_MOTHER, FAMILY_HOME_PHONE,
      FAMILY, FAMILY_MOTHER, FAMILY_HOME_PHONE_1, FAMILY_HOME_PHONE_2, 
      # FAMILY_MOBILE_PHONE, FAMILY_EMAIL, STATUS, 
      FAMILY_MOBILE_PHONE_1, FAMILY_MOBILE_PHONE_2, 
      FAMILY_EMAIL_1, FAMILY_EMAIL_2, STATUS, 
      TUITION_CHECK_AMOUNT, TUITION_CHECK_NUM, TUITION_CHECK_STATUS, 
      ONDUTY_CHECK_NUM, ONDUTY_CHECK_STATUS, 
      DONATION, DONATION_CHECK_NUM, DONATION_STATUS, 
      AGREE_TO_TERM_AND_CONDITIONS, 
      CULTURE_CLASS, CULTURE_CHOICE_1, CULTURE_CHOICE_2, CULTURE_CHOICE_3,
      MEMO
    ) = (
     'ID', 'School year', 'Class', 'Student:Chinese name', 'Student', 'POD', 
     # 'Family', 'Family:Mother', 'Family:Home phone',
     'Family', 'Family:Mother', 'Family:Home phone 1', 'Family:Home phone 2', 
     # 'Family:Mobile phone', 'Family:Email', 'Status', 
     'Family:Mobile phone 1', 'Family:Mobile phone 2', 
     'Family:Email 1', 'Family:Email 2', 'Status', 
     'Tuition check amount', 'Tuition check #', 'Tuition check status', 
     'Onduty check #', 'Onduty check status', 
     'Donation', 'Donation check #', 'Donation status', 
     'Agree to Term and Conditions', 
     'Culture Class', 'Culture choice #1', 'Culture Choice #2', 'Culture choice #3', 
     'Memo')

    with open(filename, 'rb') as csvfile:
        csvreader = csv.DictReader(csvfile)
        for row in csvreader:
            row = {k: v.strip(' \n\t') for k, v in row.iteritems()}

            student = Student.add(Student(id=row[ID], chinesename=row[STUDENT_CHINESE_NAME], name=row[STUDENT], status=row[STATUS]))

            cls = Class(row[CLASS])
            cls = Class.add(cls)
            culture = Class(row[CULTURE_CLASS].lower()) # culture class name is case insensitive
            if not culture.name: 
                culture = None
            else:
                culture = Class.add(culture)
            student.register(cls, culture)

            role = row[POD]

            tuition_check = Check(row[TUITION_CHECK_AMOUNT], row[TUITION_CHECK_NUM], row[TUITION_CHECK_STATUS])
            if not tuition_check.no and tuition_check.status in ['Received']:
                raise Exception(str(student)+' missing tuition check number')
            if tuition_check.no or tuition_check.status in ['Pending']:
                student.tuition_check = tuition_check

            pod_check     = Check(50, row[ONDUTY_CHECK_NUM], row[ONDUTY_CHECK_STATUS])
            if not pod_check.no and pod_check.status in ['Received']:
                raise Exception(str(student)+' missing onduty check number')
            if pod_check.no or pod_check.status in ['Pending']:
                student.pod_check = pod_check

            donation_check= Check(row[DONATION], row[DONATION_CHECK_NUM], row[DONATION_STATUS])
            if not donation_check.no and donation_check.status in ['Received']:
                raise Exception(str(student)+' missing donation check number')
            if donation_check.no or donation_check.status in ['Pending']:
                student.donation_check = donation_check

            if cls.isAdultClass() or role == "Adult Student":  # for adult students
                student.pod = False
                parent = Parent(student.name, student.name)  # adult's parents are his/her own
            else:
                student.pod = not (not student.isActive() or \
                                   (role and role in ["Board member", "Boardmember", "Board Member", "Teacher", "teacher", "Exempt"]) or \
                                   (not pod_check.no and pod_check.status not in ["Pending"]))
                parent = Parent(row[FAMILY_MOTHER], row[FAMILY])
            parent = Parent.add(parent)

            parent.add_phone(row[FAMILY_HOME_PHONE_1])
            parent.add_phone(row[FAMILY_HOME_PHONE_2])
            parent.add_phone(row[FAMILY_MOBILE_PHONE_1])
            parent.add_phone(row[FAMILY_MOBILE_PHONE_2])

            parent.add_email(row[FAMILY_EMAIL_1])
            parent.add_email(row[FAMILY_EMAIL_2])
            parent.add_child(student)

def __init_boardmember(filename):
    pass

def init(regcsv, bmcsv=None):
    __init_registration(regcsv)
    if bmcsv: __init_boardmember(bmcsv)


# def check():
#     # report students whose parents take AA but submit POD check
#     aa_students = set([s.name for s in Class.get("AA").students if s.isActive()])
#     for student in Student.all():
#         if not student.isActive() or not student.pod or student.parent is None: continue
        
#         mon = student.parent.mom
#         dad = student.parent.dad
#         if (mon and mon in aa_students) or (dad and dad in aa_students):
#             print >> sys.stderr, "ERROR: please exempt "+student+" from POD because his/her parent is a AA student"
#             return False
#     return True


##########################################################################################
def _proc_name_lower_upper(line):
    m = re.match(r'#(\w+)(\s*=\s*(\d+)(,(\d+))?)?', line)
    name, lower, upper = None, None, None
    if m:
        name = m.group(1).strip()
        if m.group(3):
            lower = upper = int(m.group(3))
        if m.group(5):
            upper = int(m.group(5))
    return name, lower, upper

def _slice(nslice, total):
    r = float(total)/float(nslice)
    fprev, iprev, i = 0.0, 0, 0
    while i < nslice:
        fcur = fprev+r
        if i == nslice-1:
            icur = total
        else:
            icur = round(fcur)
        yield int(icur-iprev)
        fprev, iprev, i = fcur, icur, i+1
        
class Arrangement:
    
    class NoEnoughStudent(Exception):
        def __init__(self, deficit):
            self.deficit = deficit

        def __repr__(self): 
            return repr(self)
            
    class Duty:
        def __init__(self, date, name, how_many=None):
            self.date    = date
            self.name    = name
            self.how_many = how_many
            self.students = []

        def __repr__(self):
            r = '@%s (%s) %d' % (self.date, self.name, self.n_filled())
            if self.how_many is not None:
                r += '/%d' % self.how_many
            return r

        def __str__(self):
            r = '@%s\n#%s\n'%(self.date, self.name)
            r += ''.join(str(s)+'\n' for s in self.students)
            return r

        def bootstrap(self, lower, upper=None):
            if upper is None: upper = lower
            if self.how_many is None:
                if upper <= self.n_filled():
                    self.how_many = self.n_filled()
                elif lower == upper:
                    self.how_many = lower
            elif self.how_many <= self.n_filled():
                self.how_many = self.n_filled()

        def n_filled(self):  return len(self.students)
        
        def isFilled(self): return self.how_many is not None and self.how_many == self.n_filled()

        def n_spot(self):
            if self.how_many is None: return None
            return self.how_many - self.n_filled()
            
        # def _fill_n_spot(self, pool, n, poolname):
        #     n = int(n)
        #     if n == 0: return
        #     if len(pool) < n:
        #         raise Exception('Unable to fill %d spots from %s student pool(#=%d)' % (n, poolname, len(pool)))
        #     selected = pool[:n]
        #     print >> sys.stderr, '\n'.join('+   '+str(s) for s in selected)
        #     self.students += selected
        #     del pool[:n]

        def is_student_qualified(self, student): return True

        def _fill_n_spot(self, pool, n, poolname):  # find n student from pool without parent confliction
            n = int(n)
            pj = set([ s.parent for s in self.students ])  # alread assigned
            i, m, l = 0, n, len(pool)
            while i < len(pool) and m > 0:
                s = pool[i]
                if self.is_student_qualified(s) and s.parent not in pj:
                    pj.add(s.parent)
                    selected = pool.pop(i)
                    print >> sys.stderr, '+   '+str(selected)
                    self.students.append(selected)
                    m -= 1
                    continue
                i += 1
            if m > 0: raise Arrangement.NoEnoughStudent(m)

        def fill(self, am_pool, pm_pool, am_vs_pm):  # am_vs_pm = (m, n), the rate of student from AM and PM is m:n
            if self.how_many is None:
                raise Exception('can not fill an unbootstrapped duty:' + self.__repr__())

            nspot = self.n_spot()
            if nspot == 0: return 0, 0

            print >> sys.stderr, '===== %s(%s) ====='%(self.date, self.name)
            print >> sys.stderr, '#TOFILL = %d/%d'%(nspot, self.how_many)

            am, pm = am_vs_pm
            if am == 0: 
                pm = nspot
            elif pm == 0:
                am = nspot
            else:
                r = float(am)/float(am+pm)
                am = math.ceil(nspot*r)
                pm = nspot-am

            q = []
            if am != 0: q.append( (am_pool, am, "AM") )
            if pm != 0: q.append( (pm_pool, pm, "PM") )
            
            for pool, n, poolname in q: self._fill_n_spot(pool, n, poolname)

            print >> sys.stderr, '#+AM=%d  +PM=%d'%(am, pm)
            print >> sys.stderr
            return am, pm

    class AMDuty(Duty):
        def __init__(self, date, how_many=None):
            Arrangement.Duty.__init__(self, date, "AM", how_many)

        def fill(self, am_pool, pm_pool, am_vs_pm=None):
            return Arrangement.Duty.fill(self, am_pool, pm_pool, (1, 0))

    class PMDuty(Duty):
        def __init__(self, date, how_many=None):
            Arrangement.Duty.__init__(self, date, "PM", how_many)

        def fill(self, am_pool, pm_pool, am_vs_pm=None):
            return Arrangement.Duty.fill(self, am_pool, pm_pool, (0, 1))

    class PJDuty(Duty):
        def __init__(self, date, how_many=None):
            Arrangement.Duty.__init__(self, date, "PJ", how_many)

        def is_student_qualified(self, student):
            return not student.cls.isBilingual() and \
                not student.cls.isAdultClass() and \
                student.cls.grade() > 2

    def __init__(self):
         self.duties = []
         self.dsp_lower = OrderedDict()
         self.dsp_upper = OrderedDict()

    def __str__(self):
        r = ''
        for key, value in self.dsp_lower.iteritems():
            lower, upper = value, self.dsp_upper[key]
            r += '#'+key+'='
            if lower == upper:
                r += '%d'%lower
            else:
                r += '%d,%d'%(lower, upper)
            r += '\n'
        r += '\n'
        for d in self.duties:
            r += str(d) + '\n'
        return r

    def load(self, filename):
        duty_date, duty = None, None
        # [ID=100, Foo Bao (B3P)]
        date_rep    = re.compile(r'@(\d{4})-(\d{1,2})-(\d{1,2})')
        student_rep = re.compile(r'\s*([\ \w]+)\(\s*(.+)\s*\)\s*')
        with open(filename, "rt") as cst:
            for line in cst:
                line = line.strip()
                if not line: continue

                # parse date
                m = date_rep.match(line)
                if m:
                    duty_date = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
                    duty = None
                    continue

                # global default range settings
                if duty_date is None: # global header for default parameters
                    name, lower, upper = _proc_name_lower_upper(line)
                    if lower is None or upper is None:
                        raise Exception('Improver line in the header'+line)
                    self.dsp_lower[name] = lower
                    self.dsp_upper[name] = upper
                    continue

                
                # range setting of each duty
                if line[:1] == "#":
                    if duty is not None: continue # skip
                    name, lower, upper = _proc_name_lower_upper(line)
                    how_many = None
                    if lower is not None and upper is not None: # use the value if lower == upper
                        if lower != upper:
                            print >> sys.stderr, 'WARNING: constraint ignored at "'+line+'"'
                        else:
                            how_many = lower
                    if how_many is not None and name in self.dsp_lower:  # use the default value if lower == upper
                        if self.dsp_lower[name] == self.dsp_upper[name]:
                            how_many = self.dsp_lower[name]
                    if name == "AM":
                        duty = Arrangement.AMDuty(duty_date, how_many)
                    elif name == "PM":
                        duty = Arrangement.PMDuty(duty_date, how_many)
                    elif name == "PJ":
                        duty = Arrangement.PJDuty(duty_date, how_many)
                    else:
                        duty = Arrangement.Duty(duty_date, name, how_many)
                    self.duties.append(duty)
                    continue

                # assigned student
                m = student_rep.match(line)
                if not m:  raise Exception('Not a valid student: '+line)
                sname   = m.group(1).strip()
                clsname = m.group(2).strip()
                student = Student.find(sname, clsname)
                if student is None:
                    student = Student.find(sname)
                    if student is None:
                        raise Exception('Cannot find student: '+line)

                if student.isActive():
                    if duty.name in ["AM", "PM"] and duty.name != student.cls.ampm():   # student class changed since last assignment
                        print >> sys.stderr, '-   %s  from %s (%s)' % (student, duty.date, duty.name)
                    else:
                        duty.students.append(student)
                else:
                    print >> sys.stderr, '-   %s  from %s (%s)' % (student, duty.date, duty.name)   # student withdraw since last assignment

    def _collect_avaliable_students(self):
        assigned_students = set()
        for duty in self.duties:
            assigned_students |= set( duty.students )
            
        Candidate = namedtuple('Candidate', ['student', 'prio'])
        cands = []
        limit_prio = 2   # not more than 2 duties each parent
        for parent in Parent.all():
            done   = parent.children & assigned_students
            ready  = parent.children - assigned_students
            prio = len(done)
            for s in ready:
                if prio >= limit_prio: break
                if not s.isActive() or not s.pod: continue
                cands.append( Candidate(s, prio) )
                prio += 1
        ready_students = []
        random.seed()
        for prio in range(limit_prio):
            ss = [s.student for s in cands if s.prio == prio]
            random.shuffle(ss)
            ready_students += ss
        return ready_students


    def fill_duties(self, after=date.today(), am_weight=1.0):  # am_weight: 0-pick PM only; 1-neutral; >1-inclined to picking AM
        if not self.duties:
            print >> sys.stderr, 'WARNING: There is no duty spot to fill'
            return False
            
        pool = self._collect_avaliable_students()

        am_pool = filter(lambda x: x.cls.ampm() == "AM", pool)
        pm_pool = filter(lambda x: x.cls.ampm() == "PM", pool)

        print >> sys.stderr, 'INFO: #AM pool = %s' % len(am_pool)
        print >> sys.stderr, 'INFO: #PM pool = %s' % len(pm_pool)

        #num_am_cands, num_pm_cands = len(am_pool), len(pm_pool)

        # freeze duty spot prior to after date, or with n_filled() >= dsp_upper
        for duty in self.duties:
            if duty.date < after:
                duty.bootstrap(0)  # freeze
            else:
                duty.bootstrap(self.dsp_lower[duty.name], self.dsp_upper[duty.name])

        # fill PJ duty
        for duty in self.duties:
            if duty.name != "PJ" or duty.isFilled(): continue
            duty.fill(am_pool, pm_pool, (len(am_pool)*am_weight, len(pm_pool)))  # allocate students from AM pool to PM pool in a ratio

        # fill bootstrapped duty
        for duty in self.duties:
            if duty.n_spot() is None or duty.isFilled(): continue
            duty.fill(am_pool, pm_pool, (len(am_pool)*am_weight, len(pm_pool)))

        # fill open AM/PM duties
        for ampm, pool in [("AM", am_pool), ("PM", pm_pool)]:
            open_duties = filter(lambda d: d.name == ampm and not d.isFilled(), self.duties)
            n_duties = len(open_duties)
            n_left   = len(pool)
            n_filled = sum(d.n_filled() for d in open_duties)

            if n_duties == 0 and n_left > 0:
                print >> sys.stderr, 'ERROR: there are %d %s students not assigned, try to increase upper bound'%(n_left, ampm)
                return False

            r = float(n_filled + n_left)/float(n_duties)
            lower = self.dsp_lower[ampm]
            upper = self.dsp_upper[ampm]
            if not lower<=r<=upper:
                print >> sys.stderr, 'ERROR: average # of %s students is %f, outside range [%d,%d]'%(ampm, r, lower, upper)
                return False

            for duty, piece in zip(open_duties, _slice(n_duties, n_filled+n_left)):
                duty.bootstrap(piece)
                try:
                    duty.fill(pool, pool)
                except Arrangement.NoEnoughStudent as err:  # possible false complaint
                    if duty.n_filled() < lower:
                        print >> sys.stderr, 'ERROR: unable to fill %d %s duty spots, no enough students' % (err.deficit, duty.name)
                        return False
                
        return True
