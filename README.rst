about
=====
you're using hamster to track your work? let your hamster log your work to your favorite bugtracker. ok, JIRA & Redmine
for now :)

setup
=====
As you propably installed hamster via your systems package manager you should install this python package to your root
python environment or (and that is recommended) create a virtualenv with system-packages (to ensure this apckage can
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

It will ask you for your Jira server and login and will save that data for next starts in :code:`~/.hamster-bridge.cfg`.
All your hamster tasks will be added to the first jira issue found in the hamster activity title.

license
=======
MIT-License, see LICENSE file.