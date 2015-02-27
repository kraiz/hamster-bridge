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
* When you're done, stop this task.

When you stop, the hamster-bridge becomes active and search for a valid ticket name. For JIRA that's something like
"ABC-34" (the actually regex is `[A-Z][A-Z0-9]+-[0-9]+`). It will search the title first, when there's none, it
looks into the tags. It will use the issue name only when it really exists, f.e. in a task with the title "Fixing the
STUDIO-54 error message" with the tag "DISCO-433", there will be an existence check of "STUDIO-54", if it does not exist
it will read through to issue in the tag.
Once *one* valid ticket is found, the hamster-bridge will log the spent time to this issue together with the hamster
task description as comment.

Problems? Don't work for you? Open up an `issue on GitHub <http://docutils.sourceforge.net/rst.html>`_ together with the
debug output (start the bridge with "-d").

license
=======
MIT-License, see LICENSE file.