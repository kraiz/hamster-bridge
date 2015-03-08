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

Problems? Don't work for you? Open up an `issue on GitHub <https://github.com/kraiz/hamster-bridge/issues>`_ together with the
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
