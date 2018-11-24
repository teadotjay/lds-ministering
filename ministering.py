import requests
import json
import getpass
import re
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
    
    

class MinisteringSession:
  def __init__(self):
    self._session = None
    self._assignments = None

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

  def download_assignments(self):
    if not self.check_login():
      self.login()

    url = 'https://lcr.lds.org/ministering-proposed-assignments?lang=eng&type=EQ'
    r = self._session.get(url)

    # parse response to get json encoded sandbox assignments
    m = re.search(r'__NEXT_DATA__ = ({.*})$', r.text, re.MULTILINE)
    if m:
      json_string = m.group(1)
      all_data = json.loads(json_string)
      self._assignments = all_data['props']['initialState']['ministeringData']
      return MinisteringAssignments(self._assignments)
    else:
      raise ValueError("Could not parse response from lds.org")

  def create_companionship(self, district, ministers, assignments=[]):
    if not self.check_login():
      self.login()
    minister_string = [{'personUuid': x.id, 'legacyCmisId': x.legacy_id, 'overrideWarnings': True} for x in ministers]
    assignment_string = [{'personUuid': x.id, 'legacyCmisId': x.legacy_id, 'overrideWarnings': True} for x in assignments]
    data = {
      'district': {'uuid': district.id},
      'ministeringPeople': minister_string,
      'assignments': assignment_string,
      'uuid': None}
    url = 'https://lcr.lds.org/services/umlu/v1/ministering/sandbox-companionship?lang=eng'
    headers = {'content-type': 'application/json;charset=UTF-8'}
    r = self._session.put(url, json=data)
    if r.status_code != 201:
      raise ValueError(r.text)

  def copy_companionships(self, from_districts, to_district, copy_assignments=False):
    for district in from_districts:
      for companionship in district.companionships:
        print('Copying %s from %s to %s' % (companionship, district, to_district))
        if copy_assignments:
          self.create_companionship(to_district, companionship.ministers, companionship.assignments)
        else:
          self.create_companionship(to_district, companionship.ministers)
    
  def testCreateCompanionship(self):
    if not self.check_login():
      self.login()
    data = {'assignments': [],
      'district': {'uuid': '537ecb92-4d6b-468f-ae4a-16c0d344d8f2'},
      'ministeringPeople': [{'legacyCmisId': 1916828374,
        'overrideWarnings': True,
        'personUuid': '482a7a32-77ac-49d2-a304-d27c29704a57'},
        {'legacyCmisId': 17100258170,
        'overrideWarnings': True,
        'personUuid': '1c6cde33-9f01-44c3-8dd0-3a56386ef2e9'}],
      'uuid': None}
    jsondata = '{"uuid":null,"ministeringPeople":[{"personUuid":"482a7a32-77ac-49d2-a304-d27c29704a57","legacyCmisId":1916828374,"overrideWarnings":true},{"personUuid":"1c6cde33-9f01-44c3-8dd0-3a56386ef2e9","legacyCmisId":17100258170,"overrideWarnings":true}],"assignments":[{"personUuid":"482e29fe-1b4a-4576-ab57-4e001001387c","legacyCmisId":6432894535},{"personUuid":"8b3f7f61-8f49-43b3-b576-e5e645f3d0cb","legacyCmisId":28375268170}],"district":{"uuid":"537ecb92-4d6b-468f-ae4a-16c0d344d8f2"}}'
    url = 'https://lcr.lds.org/services/umlu/v1/ministering/sandbox-companionship?lang=eng'
    headers = {'content-type': 'application/json;charset=UTF-8'}
    #r = requests.put(url, data=jsondata, headers=headers, cookies=self._cookies)
    r = requests.put(url, json=data, cookies=self._cookies)
    self._cookies = r.cookies
    return r
    
  def save_assignments(self, filename='ministering_assignments.json'):
    if self._assignments is None:
      self.download_assignments()
    with open(filename, 'w') as fp:
      json.dump(self._assignments, fp)

  def load_assignments(self, filename='ministering_assignments.json', dataset='elders'):
    with open(filename, 'r') as fp:
      self._assignments = json.load(fp)
    return MinisteringAssignments(self._assignments, dataset)

  def save_session(self, filename='ministering_session.json'):
    if self._session is None:
      self.login()
    with open(filename, 'w') as fp:
      json.dump(requests.utils.dict_from_cookiejar(self._session.cookies), fp)

  def load_session(self, filename='ministering_session.json'):
    with open(filename, 'r') as fp:
      self._session = requests.session()
      self._session.cookies = requests.utils.cookiejar_from_dict(json.load(fp))

    return self


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
      ('Load assignments from disk', ms.load_assignments),
      ('Save assignments to disk', ms.save_assignments),
      ('Download assignments from lds.org', ms.download_assignments),
      ('Display district', displayDistrict)
    ]

    items, actions = zip(*menuitems)
    choice = m.menu("Select an option below:", items)
    actions[choice-1]()


  # initialize session
  ms = MinisteringSession()

  # load previous session and data from disk
  ma = ms.load_assignments()
  ms.load_session()

  # display menu
  # while True:
  #   initialMenu()
