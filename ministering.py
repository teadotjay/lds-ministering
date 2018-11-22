import requests
import json
import getpass
import re
from collections import namedtuple

class Person:
  __slots__ = {'_name', '_email', '_id', '_legacyid'}
  def __init__(self, name, email, id, legacyid):
    self._name = name
    self._email = email
    self._id = id
    self._legacyid = legacyid
  def __repr__(self):
    return "%s(%s)" % (self.__class__.__name__, self._name)
  @property
  def name(self): return self._name
  @property 
  def email(self): return self._email
  @property 
  def id(self): return self._id
  @property 
  def legacyid(self): return self._legacyid

class Session:
  def __init__(self):
    self._session = None
    self._username = None
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

    self._cookies = r.cookies
    self._username = username

    return self


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
      data = json.loads(json_string)
      assignments = data['props']['initialState']['ministeringData']
      self._assignments = assignments
      return self
    else:
      raise ValueError("Could not parse response from lds.org")


  def get_districts(self, dataset='elders'):
    if self._assignments is None:
      self.download_assignments()
    # get districts
    district_list = []
    districts = self._assignments[dataset]
    for district in districts:
      District = namedtuple("District", "name uuid supervisor_name supervisor_uuid")
      district_list.append(District(
        name = district['districtName'],
        uuid = district['districtUuid'],
        supervisor_name = district['supervisorName'],
        supervisor_uuid = district['supervisorPersonUuid']))
    return district_list


  def get_companionships(self, district_uuids=None, dataset='elders'):
    if district_uuids:
      matches = [x for x in self._assignments[dataset] if x['districtUuid'] in district_uuids]
    else:
      matches = self._assignments[dataset]

    Companionship = namedtuple("Companionship", "uuid district_uuid ministers assignments")

    companionship_list = []

    for district in matches:
      if 'companionships' in district:
        for companionship in district['companionships']:
          minister_list = []
          for minister in companionship['ministers']:
            if 'email' in minister:
              email = minister['email']
            else:
              email = None
            minister_list.append(Person(
              name=minister['name'], email=email,
              id=minister['personUuid'], legacyid=minister['legacyCmisId']))
        
          assignment_list = []
          if 'assignments' in companionship:
            for assignment in companionship['assignments']:
              if 'email' in assignment:
                email = assignment['email']
              else:
                email = None
              assignment_list.append(Person(
                name=assignment['name'], email=email,
                id=assignment['personUuid'], legacyid=assignment['legacyCmisId']))

          companionship_list.append(Companionship(
            uuid=companionship['id'], district_uuid=district['districtUuid'],
            ministers=minister_list, assignments=assignment_list))

    return companionship_list


  def create_companionship(self, district_uuid, minister_uuids, assignment_uuids=[]):
    if not self.check_login():
      self.login()
    ministers = [{'personUuid': x, 'overrideWarnings': True} for x in minister_uuids]
    assignments = [{'personUuid': x, 'overrideWarnings': True} for x in assignment_uuids]
    data = {
      'district': {'uuid': district_uuid},
      'ministeringPeople': ministers,
      'assignments': assignments,
      'uuid': None}
    jsondata = json.dumps(data)
    url = 'https://lcr.lds.org/services/umlu/v1/ministering/sandbox-companionship?lang=eng'
    headers = {'content-type': 'application/json;charset=UTF-8'}
    r = requests.put(url, json=data, cookies=self._cookies)
    self._cookies = r.cookies
    return r
    
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
    

  def load_assignments(self, filename='ministering_assignments.json'):
    with open(filename, 'r') as fp:
      self._assignments = json.load(fp)
    return self


  def save_session(self, filename='ministering_session.json'):
    if self._cookies is None:
      self.login()
    with open(filename, 'w') as fp:
      json.dump(requests.utils.dict_from_cookiejar(self._cookies), fp)


  def load_session(self, filename='ministering_session.json'):
    with open(filename, 'r') as fp:
      self._cookies = requests.utils.cookiejar_from_dict(json.load(fp))
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
  ms = Session()

  # load previous session and data from disk
  ms.load_assignments()
  ms.load_session()

  # display menu
  # while True:
  #   initialMenu()
