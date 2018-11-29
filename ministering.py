import requests
import json
import getpass
import re
import random
from collections import namedtuple

class District:
    __slots__ = {'_id', '_name', '_supervisor', '_companionships'}
    def __init__(self, id, name, supervisor, companionships):
        self._id = id
        self._name = name
        self._supervisor = supervisor
        self._companionships = companionships
    def __repr__(self):
        return '%s("%s")' % (self.__class__.__name__, self._name)
    @property
    def id(self): return self._id
    @property 
    def name(self): return self._name
    @property 
    def supervisor(self): return self._supervisor
    @property 
    def companionships(self): return self._companionships


class Person:
    __slots__ = {'_name', '_email', '_id', '_legacy_id'}
    def __init__(self, id, legacy_id, name=None, email=None):
        self._id = id
        self._legacy_id = legacy_id
        self._name = name
        self._email = email
    def __repr__(self):
        return '%s("%s")' % (self.__class__.__name__, self._name)
    @property
    def name(self): return self._name
    @property 
    def email(self): return self._email
    @property 
    def id(self): return self._id
    @property 
    def legacy_id(self): return self._legacy_id


class Companionship:
    __slots__ = {'_id','_name','_ministers','_assignments'}
    def __init__(self, id, name, ministers, assignments):
        self._id = id
        self._name = name
        self._ministers = ministers
        self._assignments = assignments
    def __repr__(self):
        return '%s("%s")' % (self.__class__.__name__, self._name)
    @property
    def id(self): return self._id
    @property
    def name(self): return self._name
    @property
    def ministers(self): return self._ministers
    @property
    def assignments(self): return self._assignments


class MinisteringAssignments:
    __slots__ = ['_minister_list', '_assignment_list', '_companionship_list',
        '_district_list', '_data']
    def __init__(self, data=None, dataset='elders'):
        if data:
            self.loads(data, dataset)
        else:
            self._district_list = []
            self._companionship_list = []
            self._minister_list = []
            self._assignment_list = []
    
    def get_districts(self, id=None, name=None):
        if id:
            return [x for x in self._district_list if id == x.id]
        if name:
            return [x for x in self._district_list if name in x.name]
        else:
            return self._district_list
    @property
    def districts(self):
        return self.get_districts()
    
    def get_ministers(self, id=None, name=None):
        if id:
            return [x for x in self._minister_list if id == x.id]
        if name:
            return [x for x in self._minister_list if name in x.name]
        else:
            return self._minister_list
    @property
    def ministers(self):
        return self.get_ministers()

    def get_assignments(self, id=None, name=None):
        if id:
            return [x for x in self._assignment_list if id == x.id]
        if name:
            return [x for x in self._assignment_list if name in x.name]
        else:
            return self._assignment_list
    @property
    def assignments(self):
        return self.get_assignments()

    def get_companionships(self, id=None, name=None):
        if id:
            return [x for x in self._companionship_list if id == x.id]
        if name:
            return [x for x in self._companionship_list if name in x.name]
        else:
            return self._companionship_list
    @property
    def companionships(self):
        return self.get_companionships()

    def loads(self, data, dataset='elders'):
        self._data = data[dataset]
        self._district_list = []
        self._companionship_list = []
        self._minister_list = []
        self._assignment_list = []

        # process districts
        district_list = []
        for district in data[dataset]:
            companionship_list = []
                
            if 'companionships' in district:
                for companionship in district['companionships']:
                    # process ministers
                    minister_list = []
                    for person in companionship['ministers']:
                        if 'email' in person:
                            email = person['email']
                        else:
                            email = None
                        personObj = Person(
                            name = person['name'],
                            email = email,
                            id = person['personUuid'],
                            legacy_id = person['legacyCmisId'])
                        minister_list.append(personObj)
                        self._minister_list.append(personObj)

                    # process assignments
                    assignment_list = []
                    if 'assignments' in companionship:
                        for person in companionship['assignments']:
                            if 'email' in person:
                                email = person['email']
                            else:
                                email = None
                            personObj = Person(
                                name = person['name'],
                                email = email,
                                id = person['personUuid'],
                                legacy_id = person['legacyCmisId'])
                            assignment_list.append(personObj)
                            self._assignment_list.append(personObj)

                    # add companionship record
                    companionshipObj = Companionship(
                        id = companionship['id'],
                        name = " and ".join([x.name for x in minister_list]),
                        ministers = minister_list,
                        assignments = assignment_list)
                    companionship_list.append(companionshipObj)
                    self._companionship_list.append(companionshipObj)

            # add supervisor record
            supervisorObj = Person(
                id = district['supervisorPersonUuid'],
                legacy_id = district['supervisorLegacyCmisId'],
                name = district['supervisorName'],
                email = None)

            # add district record
            districtObj = District(
                name = district['districtName'],
                id = district['districtUuid'],
                supervisor = supervisorObj,
                companionships = companionship_list)
            self._district_list.append(districtObj)
 
        return self


class MinisteringEligible:
    __slots__ = ['_minister_list', '_assignment_list', '_data']
    def __init__(self, data=None, dataset='eligibleMinistersAndAssignments'):
        if data:
            self.loads(data, dataset)
        else:
            self._minister_list = []
            self._assignment_list = []
            self._data = None
    
    def get_ministers(self, id=None, name=None):
        if id:
            return [x for x in self._minister_list if id == x.id]
        if name:
            return [x for x in self._minister_list if name in x.name]
        else:
            return self._minister_list
    @property
    def ministers(self):
        return self.get_ministers()

    def get_assignments(self, id=None, name=None):
        if id:
            return [x for x in self._assignment_list if id == x.id]
        if name:
            return [x for x in self._assignment_list if name in x.name]
        else:
            return self._assignment_list
    @property
    def assignments(self):
        return self.get_assignments()

    def loads(self, data, dataset='eligibleMinistersAndAssignments'):
        data = data[dataset]
        self._data = data
        self._minister_list = []
        self._assignment_list = []
        self._data = None

        # process ministers
        minister_list = []
        if 'eligibleMinisters' in data:
            for person in data['eligibleMinisters']:
                if 'email' in person:
                    email = person['email']
                else:
                    email = None
                personObj = Person(
                    name = person['name'],
                    email = email,
                    id = person['personUuid'],
                    legacy_id = person['legacyCmisId'])
                minister_list.append(personObj)
                self._minister_list.append(personObj)

            # process assignments
            assignment_list = []
            if 'eligibleAssignments' in data:
                for person in data['eligibleAssignments']:
                    if 'email' in person:
                        email = person['email']
                    else:
                        email = None
                    personObj = Person(
                        name = person['name'],
                        email = email,
                        id = person['personUuid'],
                        legacy_id = person['legacyCmisId'])
                    assignment_list.append(personObj)
                    self._assignment_list.append(personObj)

        return self
        
        

class MinisteringSession:
    def __init__(self):
        self._session = None
        self._data = None
        self._assignments = None
        self._eligibles = None
        self._dataset = None
        self._stale = True

    def login(self, username=None, password=None):
        if username==None:
            username = input('Username: ')
        if password==None:
            password = getpass.getpass('Password: ')

        payload = {'username': username, 'password': password}
        self._session = requests.session()
        r = self._session.post('https://signin.lds.org/login.html', data=payload)

        if not '<meta http-equiv="refresh"' in r.text:
            raise PermissionError("Login failed")

    def check_login(self):
        if self._session is None:
            return False
        r = self._session.get('https://account.lds.org/features')
        if r.status_code==200:
            return True
        else:
            return False

    def download_assignments(self, dataset='elders'):
        if not self.check_login():
            self.login()

        if dataset in ['elders', 'currentElders']:
            url = 'https://lcr.lds.org/ministering-proposed-assignments?lang=eng&type=EQ'
        else:
            raise ValueError("Currently only the 'elders' dataset is supported")

        print("Downloading ministering assignments from", url)
        r = self._session.get(url)

        # parse response to get json encoded sandbox assignments
        m = re.search(r'__NEXT_DATA__ = ({.*})$', r.text, re.MULTILINE)
        if m:
            json_string = m.group(1)
            all_data = json.loads(json_string)
            self._data = all_data['props']['initialState']['ministeringData']
            self._assignments = MinisteringAssignments(self._data, dataset)
            self._eligibles = MinisteringEligible(self._data)
            self._dataset = dataset
            self._stale = False
        else:
            raise ValueError("Could not parse response from lds.org")

    def create_companionship(self, district, ministers, assignments=[]):
        self.update_companionship(district, None, ministers, assignments)

    def update_companionship(self, district, companionship, ministers, assignments=[]):
        if not self.check_login():
            self.login()
        minister_string = [{'personUuid': x.id, 'legacyCmisId': x.legacy_id, 'overrideWarnings': True} for x in ministers]
        assignment_string = [{'personUuid': x.id, 'legacyCmisId': x.legacy_id, 'overrideWarnings': True} for x in assignments]
        if companionship is None:
            uuid = None
        else:
            uuid = companionship.id
        data = {
            'district': {'uuid': district.id},
            'ministeringPeople': minister_string,
            'assignments': assignment_string,
            'uuid': uuid}
        url = 'https://lcr.lds.org/services/umlu/v1/ministering/sandbox-companionship?lang=eng'
        headers = {'content-type': 'application/json;charset=UTF-8'}
        r = self._session.put(url, json=data)
        self._stale = True
        
        if uuid == None:
            good_code = 201
        else:
            good_code = 200
        if r.status_code != good_code or 'assignmentErrors' in json.loads(r.text):
            raise ValueError((r.status_code, r.text))

    def copy_companionships(self, from_districts, to_district, preview=False):
        """Copy companionships from from_districts to to_district, optionally
        previewing the result before committing

        Example:
        Copy companionships from first three districts to the sixth
        >>> ms.copy_companionships(ms.assignments.districts[0:3], 
        >>>         ms.assignments.districts[5], preview=False)
        """
        for district in from_districts:
            for companionship in district.companionships:
                print('Copying %s from %s to %s' % (companionship, district, to_district))
                if not preview:
                    self.create_companionship(to_district, companionship.ministers)
        
    def distribute_assignments(self, to_district, eligible_assignments=None, 
            preview=False):
        """Distribute eligible assignees among companionships in to_district

        Keyword arguments:
        to_district -- district with companionships to distribute assignments 
                       among
        eligibles -- list of eligible assignments to distribute 
                     (default: None, loads list of eligible assignments
                     from database)
        preview -- set to True to preview the output without making any changes

        Example:
        Distribute unassigned households to the companionships in district 6
        >>> ms.distribute_assignments(ms.assignments.districts[5])
        """
        if eligible_assignments is None:
            eligible_assignments = self.unassigned_households
        
        # initialize new_assignments with current assignments
        new_assignments = {}
        companionships_by_id = {}
        for companionship in to_district.companionships:
            new_assignments[companionship.id] = companionship.assignments.copy()
            companionships_by_id[companionship.id] = companionship

        # populate new_assignments in levels, assigning each eligible to 
        # an existing companionship at random, if that companionship does not
        # already have a number of assignments equal to the current level
        level = 1
        while len(eligible_assignments)>0:
            for key,val in new_assignments.items():
                if len(eligible_assignments)<=0:
                    continue
                if len(val) < level:
                    # pick an eligible assignee at random
                    assignment = eligible_assignments.pop(
                            random.randrange(len(eligible_assignments)))
                    # make sure member is not assigned to minister self, else
                    # put them back on the list for the next companionship
                    mids = [x.id for x in companionships_by_id[key].ministers]
                    if assignment.id not in mids:
                        new_assignments[key].append(assignment)
                    else:
                        eligible_assignments.append(assignment)
            level = level+1

        # iterate over new assignemnts and add to database 
        for key,val in new_assignments.items():
            companionship = companionships_by_id[key]
            if len(companionship.assignments) != len(val):
                print('Updating %s with %s' % (companionship,val))
                if not preview:
                    self.update_companionship(to_district, companionship,
                            companionship.ministers, val)

        
    def save_data(self, filename='ministering_data.json'):
        if self._data is None or self._stale:
            self.download_assignments()
        with open(filename, 'w') as fp:
            json.dump(self._data, fp)

    def load_data(self, filename='ministering_data.json', dataset='elders'):
        with open(filename, 'r') as fp:
            self._data = json.load(fp)
        self._assignments = MinisteringAssignments(self._data, dataset)
        self._eligibles = MinisteringEligible(self._data)
        self._dataset = dataset
        self._stale = False

    def save_session(self, filename='ministering_session.json'):
        if self._session is None:
            self.login()
        with open(filename, 'w') as fp:
            json.dump(requests.utils.dict_from_cookiejar(self._session.cookies), fp)

    def load_session(self, filename='ministering_session.json'):
        with open(filename, 'r') as fp:
            self._session = requests.session()
            self._session.cookies = requests.utils.cookiejar_from_dict(json.load(fp))

    @property
    def assignments(self):
        if self._stale:
            self.download_assignments(self._dataset)
        return self._assignments

    @property
    def eligibles(self):
        if self._stale:
            self.download_assignments(self._dataset)
        return self._eligibles

    @property
    def unassigned_households(self):
        records = []
        for record in self.eligibles.assignments:
            assignments = self.assignments.get_assignments(id=record.id)
            if len(assignments) == 0:
                records.append(record)
        return records

    @property
    def unassigned_ministers(self):
        records = []
        for record in self.eligibles.ministers:
            ministers = self.assignments.get_ministers(id=record.id)
            if len(ministers) == 0:
                records.append(record)
        return records

if __name__ == '__main__':
    import menu3

    def display_district():
        ...

    def initialMenu():
        m = menu3.Menu(ALLOW_QUIT=True)
        menuitems = [
            ('Login', ms.login),
            ('Load session from disk', ms.load_session),
            ('Save session to disk', ms.save_session),
            ('Load assignments from disk', ms.load_data),
            ('Save assignments to disk', ms.save_data),
            ('Download assignments from lds.org', ms.download_assignments),
            ('Display district', displayDistrict)
        ]

        items, actions = zip(*menuitems)
        choice = m.menu("Select an option below:", items)
        actions[choice-1]()


    # initialize session
    ms = MinisteringSession()

    # load previous session and data from disk
    ms.load_session()
    ms.load_data()

    # display menu
    # while True:
    #     initialMenu()
