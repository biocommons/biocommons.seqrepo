Fetching existing sequence repositories
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

A public instance of seqrepo with dated snapshots is available at on
`dl.biocommons.org`.


Fetching using the seqrepo command line tool
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

The easiest way to get a new seqrepo repository is with the command line tool::

  $ seqrepo pull

The first invocation will download a complete repository.  Subsequent
invocations will pull the most recent instance, pulling only
incremental sequences.


Fetching using rsync manually
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

You can list available snapshots like so::

  $ rsync dl.biocommons.org::seqrepo                                                                                                                                                                                            
  This is the rsync service for tools and data from biocommons.org
  This service is hosted by Invitae (https://invitae.com/).
  
  drwxr-xr-x          4,096 2016/08/31 01:25:54 .
  dr-xr-xr-x          4,096 2016/08/28 03:25:40 2016-08-27
  dr-xr-xr-x          4,096 2016/08/28 15:52:54 2016-08-28

You may mirror the entire seqrepo archive or a specific snapshot, as
shown below::
  
  $ rsync -HavP dl.biocommons.org::seqrepo/2016-08-28/ /tmp/seqrepo/2016-08-28/
  
  This is the rsync service for tools and data from biocommons.org
  This service is hosted by Invitae (https://invitae.com/).

  receiving incremental file list
  2016-08-28/
  2016-08-28/aliases.sqlite3
  ...


If you have a previous snapshot, you should invoke rsync like this in
order to hard link unchanged files::

  $ rsync -HavP --link-dest=/tmp/seqrepo/2016-08-27/ dl.biocommons.org::seqrepo/2016-08-28/ /tmp/seqrepo/2016-08-28/


If seqrepo is already installed, you may check the repo status with::

  $ seqrepo -d /usr/local/share/seqrepo/2016-08-27 show-status
  seqrepo 0.2.2
  root directory: /home/reece/dl.biocommons.org/seqrepo/2016-08-27/, 7.9 GB
  backends: fastadir (schema 1), seqaliasdb (schema 1) 
  sequences: 773494 sequences, 93002629585 residues, 188 files
  aliases: 5572583 aliases, 5473096 current, 9 namespaces, 773494 sequences

For other commands, see the `command line documentation <cli.rst>`__.

.. note:: seqrepo snapshot directories may be moved, renamed, or
          symlinked as needed.  All paths are stored relative to the
          snapshot root.
