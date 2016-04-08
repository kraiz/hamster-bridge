about
=====
You're using hamster to track your work? let your hamster log your work to your favorite bug tracker. ok, JIRA & Redmine
for now :)

setup
=====
As you probably installed hamster via your systems package manager you should install this python package to your root
python environment or (and that is recommended) create a virtualenv with system-packages (to ensure this package can
talk to the hamster instance).

create virtualenv with system packages::

    virtualenv --system-site-packages path/to/hamster-bridge-env
    source path/to/hamster-bridge-env/bin/activate

JIRA
----

install via pip::

    pip install hamster-bridge

then run it with::

    hamster-bridge jira

Redmine
-------

install via pip::

    pip install hamster-bridge[redmine]

then run it with::

    hamster-bridge redmine

It will ask you for your server and login and will save that data for next starts in :code:`~/.hamster-bridge.cfg`.

usage
=====

* Start hamster and the hamster-bridge.
* Create tasks and place a JIRA/Redmine issue name inside the task title or it's tags.
* When you're done, stop this task.

When you stop, the hamster-bridge becomes active and search for a valid ticket name. For JIRA that's something like
"ABC-34" (the actually regex is `[A-Z][A-Z0-9]+-[0-9]+`). It will search the title first, when there's none, it
looks into the tags. It will use the issue name only when it really exists, f.e. in a task with the title "Fixing the
STUDIO-54 error message" with the tag "DISCO-433", there will be an existence check of "STUDIO-54", if it does not exist
it will read through to issue in the tag.
Once *one* valid ticket is found, the hamster-bridge will log the spent time to this issue together with the hamster
task description as comment.

sensitive data (passwords)
--------------------------

Since version 0.6 by default no sensitive data is stored in the config file
(e.g.  :code:`~/.hamster-bridge.cfg`). Currently the only data marked as
*sensitive* is the JIRA password.

Every time you start the application it will use all values found in the config
file and interactively ask you for the missing values (e.g. JIRA password).

If you want to force saving this *sensitive* data in the config file you can
use the **--save-passwords** option. You can also manually add the data to the
config file. If you are upgrading from an older version of **hamster-bridge**
(where all data was stored in the config file by default) then it will continue
to work like before because all required values are in the config file.

SSL/TLS certificates
--------------------

The **verify_ssl** config entry has 3 possible values: 'y' to enable
certificate verification with the default CA, 'n' to disable certificate
verification (not recommended!) and the path to a CA (Certificate Authority)
bundle containing SSL/TLS certificates. When setting a path use the **full
path** to prevent errors.

This is very valuable if the CA store that your Python environment uses by
default does not include the CA or intermediate CA that signed the certificate
of your JIRA/Redmine site. This is also the case if your JIRA/Redmine site uses
a self-signed certificate.

How to set it up? Get your certificate or certificate chain and store it in a
file. Specify the path to that file in the config.

For instance your can do this with *Google Chrome* by:

* opening your JIRA/Redmine site
* clicking on the small lock icon (View site information) in the address bar
* selecting "Connection", "Certificate information", "Details"
* clicking on "Export" and choosing "Base64-encoded ASCII, certificate chain"
* remembering the path you stored the file under and specifying that path in
  the **hamster-bridge** config

If your JIRA/Redmine site uses a certificate signed by a globally trusted root
CA you might want to try using a standard CA bundle. For example:

* With Linux Debian based systems (e.g. Ubuntu) you could use the
  path */etc/ssl/certs/ca-certificates.crt*
* Download the `certifi bundle <https://certifi.io/en/latest/>`_ and use it

For Redmine the **verify_ssl** option existed already and has been extended to
also allow you to specify a CA cert bundle path. If you had previously
specified y/n in the config it will continue to work as before.

If **verify_ssl** is set to an unknown value or to an invalid path then the
fallback is SSL/TLS certificate verification with the default CA bundle.


auto start
----------

It is possible both for JIRA and Redmine to 'auto start' (i.e. mark as in
progress or something equivalent) an issue when you start tracking time for it.

Simply set the corresponding config option to 'y' to activate auto start and to
'n' to disable it.

In the case of JIRA a third value is possible. This value implicitly assumes
'y' and uses the value you set as the name of the transition. For example if
you want to use the transition 'Working' you can set the config value to
precisely that value. The same goes if you want to the set the transition to
'In Progress'. Per default 'Start Progress' is used (i.e. when you specify
'y').


problems?
---------

Don't work for you? Open up an `issue on GitHub <https://github.com/kraiz/hamster-bridge/issues>`_ together with the
debug output (start the bridge with "-d").


hints on redmine
----------------

Redmine behaves slightly different than JIRA. For each time entry that is created, an activity has to be chosen. Within the Redmine installation a default
activity *can* be defined but usually this is not the way the installation is set up. Therefore one must be able to select the activity when creating a time
entry. As the hamster does not offer any field for such activity, we instead use the tags field.
Upon start of the hamster-bridge, all activities will be listed::

    2015-03-01 14:23:31,003    INFO: ### Available Redmine activities for using as tag value:
    2015-03-01 14:23:31,229    INFO: ### Development
    2015-03-01 14:23:31,229    INFO: ### Design
    2015-03-01 14:23:31,230    INFO: ### Deployment

If you set the name of an activity as tag, it will be used for the created time entry. If you do not specify a tag, the first activity (and usually the default
one in Redmine) will be used. If you specify more than one activity as tag value, the first found will be used (but see the hints below!).
You can mix the activity tags with other tags - the first found tag that matches the name of an activity will be used for the entry (see the hints, too).

*Important hints:*

* activity names are case sensitive
* hamster is sorting the tags alphabetically
    * if you e.g. set the tags "Development" and "Design" in this order, hamster will sort them to ['Design', 'Development'] thus the time entry will be attached to "Design"


license
=======
MIT-License, see LICENSE file.


changes
=======

0.6
---
* feature: don't store sensitive data such as passwords in the config file
  (can be overridden with **--save-passwords**)
* feature: add **verify_ssl** config option for JIRA and extend it for Redmine.
  It is now possible to specify [y/n/path] where path is the path to a CA
  certificate bundle
* feature: extend **auto_start** config option for JIRA.
  It is now possible to specify [y/n/TRANSITION_NAME] where TRANSITION_NAME is
  the name of the transition to use instead of 'Start Progress' (default)
* special thx to @omarkohl for PR #21

0.5.2
-----
* bugfix: packaging error (#19)

0.5.1
-----
* bugfix: fixed redmine missing dependency (#18)

0.5.0
-----
* feature: map hamster's task description field to jira worklog comment (#11)
* feature: improved logging a lot, added --debug switch (#12)
* feature: added flag to set the hamster check interval
* bugfix/feature: switched library from "jira-python" to "jira" to support current jira versions (#10)
* bugfix: bigger redmine reafactoring (#15, thx to @dArignac)
* bugfix: force sensitive file permissions for config file

0.4.0
-----
* feature: added support to lookup jira issue name in hamster tags (#9, thx to @toggm)

0.3.1
-----
* bugfix: console_script linking caused error starting hamster-bridge

0.3.0
-----
* new supported tracker: redmine (english & german) (contributed by dArignac)
* NEW: required positional parameter: name of bugtracker name ("jira" oder "redmine")

0.2.0
-----
* feature: autostart the jira issue when starting the task in hamster

0.1.0
-----
* feature: axtract issue from hamster activity be regex
* bugfix: logging of exceptions communicating with jira server

0.0.1
-----
* first release
