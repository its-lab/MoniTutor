# MoniTutor: Workshop Monitoring for Students

## Description

MoniTutor is a framework that provides students with a sophisticated interactive
eLearning platform for IT infrastructure related topics. It is based on the
infrastructure monitoring system Icinga2 and developed in Python.

MoniTutor is currently used at FH Aachen - University of Applied Sciences
to support students in hands-on lessons in the subject area IT-Systems (fault
tolerant systems & IT-Infrastructure).

## News, help, contact

Notable commit and announcements are posted on Twitter
[@MoniTutor](https://twitter.com/MoniTutor) and in our [mailing list](https://list.noc.fh-aachen.de/mailman/listinfo/monitutor).
.

If you are interested in contributing, please subscribe to our [mailing list](https://list.noc.fh-aachen.de/mailman/listinfo/monitutor).

Bugs and feature requests can be submitted via [github issues](https://github.com/its-lab/MoniTutor/issues). 

## Features

* Supports arbritrary scenarios on all platforms that support python2.7
  (GNU/Linux, BSD, Windows)
* Configuration via Webfrontend
* NAT/Firewall-penetration for virtual machines and remote clients
* Simple, interactive front-end for students
* Presentation-mode to display live-status

### Screenshots
![monitutor1](https://cloud.githubusercontent.com/assets/13717492/20059691/cef75b9a-a4f7-11e6-845f-e1a9635fe739.jpg)
Student view. Lists all milestones and the corrosponding checks and their
results.

![monitutor2](https://cloud.githubusercontent.com/assets/13717492/20059704/da3e70f6-a4f7-11e6-9ef6-72b8c23dae25.jpg)
Admin scenario overview. In the admin area the administrator can add and modify
scenarios.


### Infrastructure and requirements

* Server
    * Based on GNU/Linux 
    * Python version 2.7.6+
    * Based on Icinga2, Web2Py and PostgreSQL

* Client (any system a student uses in a scenario)
    * Platform independent as long as python 2.7.6+ is supported
    * To interact with the platform, a webbrowser is required
    * One-directional connection from the client to the server is required

![monitutor_arch](https://cloud.githubusercontent.com/assets/13717492/20060036/870647cc-a4f9-11e6-8015-d327b90a4ce5.png)



## Getting started

The prefered Linux distribution for this project is Debian. All packages are
installed from the official Debian repositories. For distributions other than
Debian, packages may also be available. Please contact your distribution
packagers. 

### Running MoniTutor with docker
To get MoniTutor up and running easily, you might want to check out [our docker images](http://github.com/its-lab/MoniTutor-docker). Skip to [the client setup](https://github.com/its-lab/MoniTutor#setting-up-the-monitutor-client) once the application is running.

### Installing the Base System

#### Icinga2
MoniTutor depends on Icinga2 and PostgreSQL databases. Hence, the first step is
to install Icinga2. During the installation you need to choose DB IDO
PostgreSQL. Note that PostgreSQL is our recommendation. As MoniTutor and Icinga
work on MySQL as well, you are free to use MySQL/MariaDB.
You also need to install Icingaweb2.

A sophisticated installation guide for Icinga2 can be found in the Icinga2
documentation. [Icinga2 Install-guide](http://docs.icinga.org/icinga2/latest/doc/module/icinga2/toc#!/icinga2/latest/doc/module/icinga2/chapter/getting-started#setting-up-icinga2)

After you finished the Icinga2 installation, you can continue
with the installation of Web2Py. It is recommended but optional to install icingaweb2. 

#### Web2Py
The next step is to install web2py. Web2py is a free, open-source web framework for agile development of secure database-driven web applications; it is written in Python and programmable in
Python. web2py is a full-stack framework, meaning that it contains all the components you need to build fully functional web applications. MoniTutor depends on Web2Py because it was developed as a Web2Py application.

A sophisticated installation guide for web2py can be found in the web2py
documentation. [Web2Py install-guide](http://web2py.com/books/default/chapter/29/13/deployment-recipes#Apache-setup)

### Database
Add the following to your pg_hda.conf:

```
# vim /var/lib/pgsql/data/pg_hba.conf

# monitutor
local   monitutor      monitutor                            md5 
host    monitutor      monitutor      127.0.0.1/32          md5
host    monitutor      monitutor      ::1/128               md5
local   icinga2        monitutor                            md5 
host    icinga2        monitutor      127.0.0.1/32          md5
host    icinga2        monitutor      ::1/128               md5
```

After you restarted the psql server, create a new user and database, both called
"monitutor". Choose a secure password and remember it.

```
# su postgres
# psql

postgres=# CREATE DATABASE monitutor;
postgres=# CREATE USER monitutor WITH PASSWORD 'mon!tutor123';
postgres=# ALTER DATABASE monitutor OWNER TO monitutor;
postgres=# \q

## GRANT SELECT on Icinga tables.
# psql icinga
icinga=# GRANT SELECT ON icinga_hoststatus TO monitutor ;
icinga=# GRANT SELECT ON icinga_objects TO monitutor ;
icinga=# GRANT SELECT ON icinga_customvariables TO monitutor ;
icinga=# GRANT SELECT ON icinga_hosts TO monitutor ;
icinga=# GRANT SELECT ON icinga_servicestatus TO monitutor ;
icinga=# GRANT SELECT ON icinga_statehistory TO monitutor ;
icinga=# \q
```

Verify the setup by executing:

```
psql monitutor monitutor --password
```

You should be able to login. If the login fails, make sure your password is
right, the pg_hda.conf is as expected and restart the psql server.


### Installing the web2py app

Now that the database is setup, you need to clone the MoniTutor repository and
copy it to your web2py/applications path.

```
# apt-get install git
# git clone <github-path>/monitutor.git
# mv monitutor /var/www/web2py/applications
# chown -R www-data:www-data /var/www/web2py/applications
```

We also need to install some python libraries. To do so in a convenient way, we
first need to install pip.

```
# apt install python-pip libgraphviz-dev graphviz-dev pygraphiz python-psycopg2
# pip install requests pykka sqlalchemy subprocess32
```

After everything is in place, specify the database usernames and passwords in
monitutors appconfig.ini file, which can be found in the private folder of the
applicaion (/var/www/web2py/applications/monitutor/private/appconfig.ini).

```
[monitutor_env]
database_name = monitutor
database_user = monitutor
database_password = <monitutorpassword>
icinga2_database_name = icinga
icinga2_api_user = icinga
icinga2_api_password = <icingapassword>
```

Before launching our app, configure monitutor to be the default web2py
application on your server.

```
# vim /var/www/web2py/routes.py

default_application = 'monitutor'
```

Restart your apache2 server after all these steps.

### Creating users

Try to access your application via your webbrowser. If you get error messages,
verify the content of your appconfig.ini and make sure the monitutor-database
and the icinga2-database are both reachable.
Once you have the application up and running, on the front page where it prompts
you for a login, hit register and register yourself.
After you successfully logged in, you need to add your new user to the admin
group.

```
# su postgres
# psql monitutor
monitutor=# INSERT INTO auth_membership (user_id, group_id) SELECT auth_user.id,
auth_group.id FROM auth_user, auth_group WHERE auth_user.username =
'<your-username>'
AND auth_group.role = 'admin';
```

If you now go back to the monitutor frontend, after having logged in successfully, you should see an "Admin" entry in the menu on the top of
the screen.

### Backend components

#### Icinga2 API

MoniTutor configures the underlying Icinga system via templates and its RESTful API. Hence it is mandatory to enable the API feature.

```
# icinga2 feature enable api
# icinga2 api setup
```

After restarting the Icinga daemon, the api is ready to receive commands. The
password of the root user can be found in /etc/icinga2/conf.d/api-users.conf.
**You need to copy the password** into the
web2py/applications/monitutor/models/scheduler.py file.

To verify that the API is working properly, execute the following command:

```
curl -k -s -u root:<password> 'https://localhost:5665/v1/objects/hosts' | python
-m json.tool
```

A dict, containing all icinga-hosts should be displayed on your screen.

#### Web2Py scheduler
In order for Web2Py to perform asynchronus background tasks, a worker process
needs to be set up. Information on worker processes can be found in the web2py
documentation. [Web2Py Scheduler](http://web2py.com/books/default/chapter/29/04/the-core#web2py-Scheduler)

```
python /var/www/web2py/web2py.py -K MoniTutor:init:main -v
```

Note that the worker only needs write access to the conf.d directory of icinga2. It is
recommended to not start the script as root but as the "nagios" user or another
user with access to the icinga conf.d directory.

#### MoniTutor tunnel
In order to transport and execute programs that Monitutor holds in its database,
we need to set up a bi-directional tunnel between the MoniTutor server and the
students clients. A tunneling application that does exactly this can be found
in a separate repository. [MoniTutor-Tunnel](http://github.com/its-lab/MoniTutor-Tunnel)

Just clone the repository and configure the yaml-file to match your database
setup. To enable the server and client for encrypted communication , generate a rsa
key-pair and copy your existing keys to /etc/ssl. After that is done, execute the
script. Note that security features, including the encryption, are still in early
development. In the current release, **the client does not verify the
certificate**.

```
# git clone git@149.201.46.31:swillus/monitunnel.git
# cd monitunnel
# openssl req -x509 -newkey rsa:4096 -keyout /etc/ssl/key.pem -out /etc/ssl/cert.pem -days 3650 -nodes
# # OR copy the existing key to/etc/ssl/key.pem and the cert to /etc/ssl/cert.pem
# python server.py --help

usage: server.py [-h] [-a x.x.x.x] [-p PORT] [-v] [-l]

MoniTunnel server script.

optional arguments:
  -h, --help            show this help message and exit
  -a x.x.x.x, --address x.x.x.x
                        Address to listen to (default: None)
  -p PORT, --port PORT  Listening port (default: 13337)
  -v, --verbose         Increase verbosity
  -l, --log             Increase logging level
  -d, --daemonize       Start as daemon

To use the MoniTunnel application you also need to run the client.

# python server.py -p 8080 -d -ll
```

Now, You can begin to define scenarios.
Note, that once you are finished, you need to provide your students with access to
the client.py file in order to connect to the server.

#### Setting up the Monitutor Client

In order to establish a bi-directional tunnel between the students
workshop-client and the MoniTutor server, the client needs to execute the
client.py script that comes with the server script of the monitutor tunnel
module. 

After the server.py was successfully started on the server, the client script
needs to be started with the correct IpAddress:Port pair.

```
# python client.py --help

usage: client.py [-h] -a ADDRESS [-p PORT] [-v] [-l] [-u USER] [-n HOSTNAME]

MoniTunnel client script.

optional arguments:
  -h, --help            show this help message and exit
  -a ADDRESS, --address ADDRESS
                        Server IPv4 address
  -p PORT, --port PORT  Server port (default: 13337)
  -v, --verbose         Increase verbosity
  -l, --log             Enable logging to syslog
  -u USER, --user USER  File that contains the username (default:
                        /etc/MoniTutor/username)
  -n HOSTNAME, --hostname HOSTNAME
                        [Optional]

To use the MoniTunnel application you also need to run the server. MoniTunnel
does not support IPv6 yet.

python client.py -a 10.0.0.1 -p 8080 -u ./username.txt -n testclient
```

Two further things must be configured properly in order for the client script to work.

 A "username-file" must be available that holds the MoniTutor-username of the
   student.
   ```
   echo "testuser" >> username.txt
   ```

The hostname of the system (/etc/hostname) has to be the same hostname as
defined in the corresponding monitutor system. Note that the hostname of a
system can be "faked" by using the "-n" parameter of the client script.

The MoniTutor server uses the hostname and the username to identify
connecting clients. Currently no further authentication is implemented, meaning
the clients can spoof their username easily and connect as different users
without knowing any passwords. As this is one possible attack vector,
threatening the integrity of student data on the monitutor server, a
authentication-mechanism will be implemented in the future.
## Administration

If you followed all of the previous steps, you should be able to log in as an
admin user. After logging in you should see an admin entry in the menu at the top of the
screen.

Through the admin menu, you can access 3 areas.

In the first area, you define your scenarios.
The components area gives you a brief overview over all the components that can
be assigned to a scenario.
The last area provides the administrator with an overview over student
activities.

### Systems
Before creating milestones, the administrator should define the hosts that are dealt with in the scenario. 
In MoniTutor those hosts are represented as Systems. A System can be anything that can be accessed via TCP/IP.
To create and change your system setup, go to the admin menu at the top and navigate to the component overview.
On the left side you can click on "systems" which should bring you to the systems forms.
A System always needs a hostname and IPv4 and IPv6 addresses. If none is
available, enter 127.0.0.1/::1
Note that the system configuration can be altered anytime. However it is
sometimes necessary to reinitiate a scenario after doing so.

### Milestones
A Milestone can be seen as a group of tasks that a student has to finish before
he or she is able to continue with further tasks.
The first milestone of a scenario might be the setup of the server and client
operating systems that are used. Client and server possibly need to be able to
access the internet and they probably need to be able to reach each other. All
those states can be represented by one milestone.
A second milestone in a scenario might group client and server status to get scenario specific
applications up and running. If the scenario for example introduces LDAP, the
student needs to install certain LDAP-specific packages in order to start the
actual tasks.

The overall goal should be represented by the sum of all milestones.

Once all the milestones are defined, the adminstrator continues defining
entities within a milestone that represent those specific status and requirements a
student has to satisfy. In MoniTutor those entities are defined as "checks".

### Checks

A check can be seen as an instruction on how to test the functionality of a
certain thing. A "check" might be the execution of a "ping" on one system
towards another system to test if the systems are connected properly. A check can
later be triggered by a student to assess their work themselves and to enable
them to find their mistakes easily.

Each Milestone that the administor defines holds one or more checks.

To help the student satisfy each check within a milestone, the display-name
of each check should be precise and clear to not confuse the student. "Client-A
can reach Client-B" is better than "ping a b".

Obviously the check needs to know where (which system) to audit and a
specification on how to audit the system. The "where" is satisfied by assigning
a "source" to the check. The source system is the system on which the check is
executed. The "How?" is not as easy to answer because it highly depends on your
environment. To execute the check on the Source system, we need to provide
Monitutor the source-code of a program it can execute on the host. In the end, a
Check describes which routine (program) with which parameters is executed on
which systems.

Defining a check is a 5-step process:

* Assign a display name that does not confuse your students
* Select which system the check is executed on (Source System)
* Select a program the check executes on the source system
* Specify the parameters that are passed to the program when it is executed
    * prameters may also be variables that are linked to systems. (For example
      $SOURCE.ip4_address)
    * [OPTIONAL] add a destination host and use its system configuration as
      dynamic parameters ($DEST.ip4_address or $DEST.vars.commuinty)
* [OPTIONAL] Add a hint to help the students to solve the check.

### Programs

A Program can be a small script written in an arbitrary programming languauge.
However, the interpreter that executes the program needs to be installed on the
systems and the interpreter path needs to be specified. The purpose of a program
is to programatically evaluate whether or not a certain state is present on the
host it is executed on. It is important to note that programs which acceppt
parameters are useful as they can be reused for different checks to test
different states. A simple example would be a bash script that checks the
current system time of a host.

```
#!/bin/bash
TIME=$(date)
LOCALES=$(locale | head -1)
echo $TIME, $LOCALES
```

Note that the returncode of this script is always 0 (successful) and no
parameters can be passed to the program. The example script is a useful program
to include in one check for each system in a scenario inside of the
"base-test"-Milestone when time plays an important role (Think of Kerberos or
Logging). After it is executed on a system, the student and the supervisor can see the result (in
this case the local time on the machine) in the Monitutor webinterface.

A more sophisticated example of a program that accepts parameters is the
following:

```
#!/bin/bash
dpkg --get-selections 2>&1 | grep ^$1 > /dev/null
if [ $? -ne 0 ] ; then
  echo "SW package $1 not installed"
    exit 2
    fi
    echo PASSED
    exit 0
```

The script returns a PASSED with returncode 0 if a given packet, passed to the
program as the first argument, is installed and returns an error code of 2
including a short message if it is not installed.

As these programs are only used in a non-critical environment, it is fine that
they are "quick and dirty". The general guideline when writing programs for
MoniTutor is to keep them as simple as possible.

#### MoniTutor program guideline

* Keep it simple
* Try to write generic programs which can be used for multiple checks
* Try to write programs that do not depend on additional libraries/packages
* Keep it as multi-platform as possible
* Do not rely on non-free applications/components

### Scenario initiation

Once all Milestones are filled with checks and everything else is set up as
well, the administrator needs to initiate the scenario. The Scenario initiation
can be triggered by clicking on the small power icon of a scenario on the
scenario-overview screen.
The initiation process is executed by one of the web2py-workers you started earlier,
executing the web2py.py script with a -K argument. If you didn't start a worker,
you should do it now.

The worker will create Icinga2-templates representing all your hosts and checks.
You can find all created templates on your MoniTutor server in the conf.d
directory of Icinga2 (/etc/icinga2/conf.d/monitutor/).

After the scenario is initiated (a progress bar indicates whether or not the
process finishes) you can toggle the scenarios visibility and the students can
start working on it.

If you need to delete all student data, you can click on the small rubber icon
next to a scenario on the scenario overview screen.

