changes
=======

0.5.1
-----
* bugfix: fixed redmine missing dependency (#18)

0.5.0
-----
* feature: map hamster's task description field to jira worklog comment (#11)
* feature: improved logging a lot, added --debug switch (#12)
* feature: added flag to set the hamster check interval
* bugfix/feature: switched library from "jira-python" to "jira" to support current jira versions (#10)
* bugfix: bigger redmine reafactoring (#15, thx to dArignac)
* bugfix: force sensitive file permissions for config file

0.4.0
-----
* feature: added support to lookup jira issue name in hamster tags (#9 thx toggm)

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
