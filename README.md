# lds-ministering
## Introduction
This is a Python interface to the online ministering assignments for the Church of Jesus Christ of Latter-Day Saints.
It allows automation of repetitive tasks such as copying companionships from one district to another, deleting all
companionships in a district, and distributed unassigned households among all the companionships in a district. Use
is limited to authorized members of the Church, such as bishoprics, elders quorum presidencies, and relief society
presendencies, and subject to the Church privacy policy at https://www.lds.org/legal/privacy-notice?lang=eng&country=go.

This is *not* an official library of the Church, nor is it commissioned or sanctioned by Church leadership. Updates
to the Church web site may render this library inoperable at any time. The author offers no warranty, express or implied, 
and disclaims all responsibility for the use or potential misuse of this library or any applications that may use it.

## Usage
This is a companion to the online ministering assignment tool for elders quorum presidencies provided at 
https://lcr.lds.org/ministering-proposed-assignments?lang=eng&type=EQ. (Relief society ministering assignments are not
yet supported, but can be made to work with minor modifications.) It does not offer all the capabilities of the online
assignment tool, but it is able to automate some of the more repetitive tasks, with examples given in the following 
sections. The Python library operates exclusively on the proposed assignments sandbox by design, allowing the user to 
review any changes online before publishing.

### Interactive mode
The application can run in interactive mode, which creates a new MinisteringSession, with the handle "ms", and attempts
to restore the data and cookies from a previous session, if one has been saved.

```sh
ipython -i ministering.py
```

### Logging in
The first step is to log in with your lds.org username and password. The library allows you to pass in your username and
password, but we do not recommend storing this anywhere as plaintext. Instead, if you do not pass in a username or 
password, the library will prompt you on the command line.

```
In [1]: ms.login()
Username: #######
Password:
```

### Downloading ministering data
The next step is to download the ministering data from the sandbox. Before you do so, make sure the sandbox is up-to-date
with the current assignments. There is an option at https://lcr.lds.org/ministering-proposed-assignments?lang=eng&type=EQ
to populate the sandbox with the current assignments, or to discard any unpublished changes and start over. The Python
library does not provide either capability, to avoid accidentally clobbering any changes you may have in progress.

```
In [2]: ms.download_assignments()
Downloading ministering assignments from https://lcr.lds.org/ministering-proposed-assignments?lang=eng&type=EQ
```

### Listing assigned districts and companionships
The MinisteringSession contains an `assignments` property, which returns a MinisteringAssignments object. This object
has a `districts` property that returns all districts (with or without assignments), a `companionships` property that
returns all companionships in all districts, a `ministers` property that returns all assigned ministers, and an
`assignments` property that returns all assigned households.

Districts and companionships are returned as District and Companionship records, respectively. Ministers and households
are returned as a Person record.
```
In [3]: ms.assignments.districts
Out [3]:
[District("District 1"),
 District("District 2"),
 District("District 3")]
 ```
 
 Districts also have a `companionships` property, which lists all companionships in the district.
 ```
 In [4]: ms.assignments.districts[0].companionships
 Out [4]:
 [Companionship("Priesthood, Peter and Moriankumr, Mahonri"),
  Companionship("Mormon, Mark and Mormon, Molly")]
```

Districts also have properties for their unique `id`, `name`, and `supervisor`.
