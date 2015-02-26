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

install via pip::

    pip install hamster-bridge

then run it with::

    hamster-bridge jira

or::

    hamster-bridge redmine

It will ask you for your JIRA server and login and will save that data for next starts in :code:`~/.hamster-bridge.cfg`.

usage
=====
* Start hamster and the hamster-bridge.
* Create tasks and place a JIRA/Redmine issue name inside the task title or it's tags.
* As soon as you stop the task in hamster, the hamster-bridge should detect this, find the issue and log the spent time
  to your JIRA/Redmine server.

Problems? Don't work for you? Open up an issue here together with the debug output (start the bridge with "-d").

license
=======
MIT-License, see LICENSE file.