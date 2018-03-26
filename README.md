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
![milestone](https://user-images.githubusercontent.com/13717492/37915630-417302e6-311a-11e8-9d20-aebc1dcae667.png)
Student view. Lists all milestones, the corrosponding checks and their results.

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

## Getting started

The prefered Linux distribution for this project is Debian. All packages are
installed from the official Debian repositories. For distributions other than
Debian, packages may also be available. Please contact your distribution
packagers. Even though all components can be installed manually, it is recommended to install the application via docker.

### Running MoniTutor with docker
To get MoniTutor up and running easily, use [our docker images](http://github.com/its-lab/MoniTutor-docker). Skip to [the client setup](https://github.com/its-lab/MoniTutor#setting-up-the-monitutor-client) once the application is running.

#### Setting up the MoniTutor Client

In order to establish a bi-directional tunnel between the student's
workshop-client and the MoniTutor server, the client needs to execute the
client application that comes with the server script of the [monitutor tunnel
application](https://github.com/its-lab/MoniTutor-Tunnel).

Make sure, that all students execute the client application with valid parameters. Use `python start_client.py --help` to get a list of all parameters.

Buttons on the upper right corner in the student webinterfaceinfe indicatee which systems are connected.

![host_indicator](https://user-images.githubusercontent.com/13717492/37915958-ec7fc278-311a-11e8-8109-227e6ef34eb6.png)

When hovering over the indicator icons, the names of the systems are shown.

## Administration

After installing the application, you need to register an account. To do that, simply click on the `register` button on the login page and fill out the form. Once the registration is finished, Open [web2py's database administration](https://localhost/MoniTutor/appadmin/select/tutordb?query=tutordb.auth_membership.id%3E0) and add your user to the admin group. After doing this, you should notice and `Admin` menu on top of the screen after you logged in with your user account.

Through this Admin menu, you can access 4 areas.

The Dashboard area is still in development. It provides quick access to overview screens.
In the Scenario area, you define your scenarios.
The components area gives you a brief overview over all the components that can
be assigned to a scenario.
The last area provides the administrator with an overview over student
activities.

### Systems
Before creating milestones, the administrator should define the hosts that are dealt with in the scenario. 
In MoniTutor those hosts are represented as Systems. A System can be anything that can be accessed via Network.
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
A second milestone in a scenario might consist of client and server states that are mandatory to get scenario specific
applications up and running. If the scenario for example introduces LDAP, the
student needs to install certain LDAP-specific packages in order to start the
actual tasks.

The overall goal should be represented by the sum of all milestones.

Once all the milestones are defined, the adminstrator continues defining
entities within a milestone that represent specific states and requirements a
system has to satisfy. In MoniTutor those entities are called "checks".

### Checks

A check can be seen as an instruction on how to test the functionality of a
certain thing. A "check" might be the execution of a `ping` on one system
towards another system to test if the systems are connected properly. A check can
later be triggered by a student to assess their work themselves and to enable
them to find their mistakes easily.

Each Milestone that the administor defines holds one or more checks.

To help the student satisfy each check within a milestone, the display-name
of each check should be precise and clear to not confuse the student. "Client-A
can reach Client-B" is better than "ping a b".

Obviously the check needs to know where (which system) to audit and a
specification on how to audit the system. The "where?" is satisfied by assigning
a "source" to the check. The source system is the system on which the check is
executed. The "How?" is not as easy to answer because it highly depends on your
environment. To execute the check on the Source system, you need to provide
the source-code of a program that can be executed on the source system. In the end, a
Check describes which routine (program) with which parameters is executed on
which systems.

Defining a check is a 5-step process:

* Assign a display name that does not confuse your students
* Select which system the check is executed on (Source System)
* Select a program the check executes on the source system
* Specify the parameters that are passed to the program when it is executed
    * prameters may also be variables that are linked to systems. (For example
      $SOURCE.ip4_address)
    * [OPTIONAL] add a destination host and use it's system configuration as
      dynamic parameters ($DEST.ip4_address or $DEST.vars.commuinty)
* [OPTIONAL] Add a hint to help the students to solve the check.

### Programs

A Program can be a small script written in an arbitrary programming languauge.
However, the interpreter that executes the program needs to be installed on the
systems and the interpreter path needs to be specified. The purpose of a program
is to programatically evaluate whether or not a certain state is present. It is important to note that programs which acceppt
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
this case the local time on the machine) in the MoniTutor webinterface.

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

### Scenario initiation

Once all Milestones are filled with checks and everything else is set up as
well, the administrator needs to initiate the scenario. The Scenario initiation
can be triggered by clicking on the small power icon of a scenario on the
scenario-overview screen.

The worker will create Icinga2-templates representing all your hosts and checks.
You can find all created templates on your MoniTutor server in the conf.d
directory of Icinga2 (/etc/icinga2/conf.d/monitutor/).

After the scenario is initiated (a progress bar indicates if
process finishes) you can toggle the scenario visibility and the students can
start working on it.

If you need to delete all student data, you can click on the small rubber icon
next to a scenario on the scenario overview screen.
