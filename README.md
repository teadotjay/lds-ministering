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

```python
In  [1]: ms.login()
Username: #######
Password:
```

### Downloading ministering data
The next step is to download the ministering data from the sandbox. Before you do so, make sure the sandbox is up-to-date
with the current assignments. There is an option at https://lcr.lds.org/ministering-proposed-assignments?lang=eng&type=EQ
to populate the sandbox with the current assignments, or to discard any unpublished changes and start over. The Python
library does not provide either capability, to avoid accidentally clobbering any changes you may have in progress.

```
In  [2]: ms.download_assignments()
Downloading ministering assignments from https://lcr.lds.org/ministering-proposed-assignments?lang=eng&type=EQ
```

Library functions that modify online data will trigger an automatic re-download of the database on any subsequent data
access. However, if you or someone else makes changes on the web site, you will need to manually re-download in order for 
the MinisteringSession to reflect any changes the library doesn't know about.

### Listing assigned districts and companionships
The MinisteringSession contains an `assignments` property, which returns a MinisteringAssignments object. This object
has a `districts` property that returns all districts (with or without assignments), a `companionships` property that
returns all companionships in all districts, a `ministers` property that returns all assigned ministers, and an
`assignments` property that returns all assigned households.

Districts and companionships are returned as District and Companionship records, respectively. Ministers and households
are returned as a Person record.
```python
In  [3]: ms.assignments.districts
Out [3]:
[District("District 1"),
 District("District 2"),
 District("District 3")]
 ```
 
Districts also have a `companionships` property, which lists all companionships in the district.
```python
In  [4]: ms.assignments.districts[0].companionships
Out [4]:
[Companionship("Priesthood, Peter and Moriankumr, Mahonri"),
 Companionship("Mormon, Mark and Mormon, Molly")]
```

Districts also have properties for their unique `id`, `name`, and `supervisor`.

Companionships also have a unique `id` and `name`, which is populated from the names of its `ministers`.
```python
In  [5]: ms.assignments.districts[0].companionships[0].ministers
Out [5]: [Person("Priesthood, Peter"), Person("Moriankumr, Mahonri")]
```

If the companionship has any household assignments, the `assignments` property will list them.
```python
In  [6]: ms.assignments.districts[0].companionships[0].assignments
Out [6]: [Person("Active, Les")]
```

Finally, the Person record, used for both ministers and households, lists the person's unique `id` in the system,
their `name` (sometimes combined with spouse's name), and `email` address, if available.

### Listing all or unassigned ministers and households
The `assignments` property lists only assigned members; the `eligible` property lists all eligible ministers and
households (those capable of ministering or ministered to within the current organization, e.g. elders quorum).

The `eligibles` property returns a MinisteringEligible object, which has properties `ministers` and `assignments`
similar to a MinisteringAssignments object.

You can also filter ministers and assignments (households) by `name` or `id`. Searching by name includes all records 
that contain the string specified in the `name` argument.
```python
In  [7]: ms.eligibles.get_assignments(name='Active')
Out [7]: [Person("Active, Les"), Person("Active, Moe")]
```

To get the list of unassigned ministers and households, use the `unassigned_ministers` or `unassigned_households`
property of the MinisteringSession object.

### Creating, modifying, and deleting companionships
At this time, you cannot add or remove districts; you'll need to use the online tool for that. You can, however,
create, modify, and delete companionships. When you create or modify a companionship, you provide the district
for that companionship, a list of ministers, and an optional list of households. (If households are not specified,
this creates an empty companionship.)

For example, the code below creates a new companionship using the first two unassigned ministers and assigns all 
unassigned households to these two poor souls. (Don't actually do this.)

```python
district = ms.assignments.districts[1]  # selects second district
minister1 = ms.unassigned_ministers[0]  # selects the first unassigned minister
minister2 = ms.unassigned_ministers[1]  # selects the first unassigned minister
households = ms.unassigned_households   # selects all unassigned households
ms.create_companionship(district, ministers=[minister1, minister2], assignments=households)
```

Similarly, the code below edits an existing companionship at random from one of the first three districts, adding
an unassigned household at random. (Don't do this either, unless you want an angry bishopric.)

```python
district = random.choice(ms.assignments.districts[0:3])
companionship = random.choice(district.companionships)
new_household = random.choice(ms.unassigned_households)
households = companionship.assignments + [new_household]
ms.update_companionship(district, companionship, companionship.ministers, households)
```

Deleting a companionship is simple; you need only provide the Companionship object. Note: this deletes the 
companionship and un-assigns its ministers and households. Be sure you know what you're doing. (You can always 
discard the changes in the sandbox if you make a mistake, as long as you have not yet published them.)

```python
ms.delete_companionship(my_companionship)
```

You can also delete *all* the companionships in the district, for example, if you want to start over and re-populate
them. The section below gives some examples of this.

```python
ms.delete_companionships(my_district)
```

### Copying companionships from one district (or more) to another
If your ward uses districts to further subdivide companionships (primary route vs. texting route, etc.), the
`copy_companionships` function may be useful. It copies all the companionships from one or more districts
into another existing district. (Note: this does not check for duplicates, so be careful.) This command
includes a `preview` argument so that you can preview the changes before making them in the sandbox.

The following code copies companionships (but not their assignments) from districts 1-3 into district 6.

```python
ms.copy_companionships(ms.assignments.districts[0:3], ms.assignments.districts[5], preview=False)
```

### Distributing unassigned households among all the companionships in a district
OK, this one is a little application-specific, but we use it in our ward to make sure all "unassigned" households
at least have someone identified as a point of contact. It distributes the `unassigned_households` evenly and
randomly among the companionships of a given district, respecting any assignments that already exist.

Our ward uses district 6 for this purpose:

```python
ms.distribute_assignments(ms.assignments.districts[5], preview=False)
```
