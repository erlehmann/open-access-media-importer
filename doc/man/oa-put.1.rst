======
oa-put
======

--------------------------------------------
Open Access Media Importer upload operations
--------------------------------------------

:Author: Nils Dagsson Moskopp <nils@dieweltistgarnichtso.net>
:Date: 2015-01-27
:Manual section: 1

SYNOPSIS
========

oa-put [--force-upload] {upload-media} [source]

oa-put -h

DESCRIPTION
===========

oa-put can upload metadata and media of resources indexed with the
Open Access Media Importer (OAMI), which are usually supplementary
materials of scientific papers. oa-put does not upload the original
media files, but files that OAMI converted to royalty-free formats.

All oa-cache sub-commands need internet access.

upload-media
    upload-media is used to upload converted media of a given source
    to a MediaWiki instance configured in the OAMI configuration file
    ("$HOME/.config/open-access-media-importer/userconfig"). oa-put
    creates a Wiki page for each media file containing its metadata.


OPTIONS
=======

--force-upload
    Force upload of supplementary materials already uploaded.
    This option is useless unless given with command "upload-media".

-h --help
    Show a short usage summary.

-v --verbose
    Increase verbosity. This option can be given multiple times.


BUGS
====

"upload-media" will crash if the MediaWiki login data is wrong.

When OAMI has no materials indexed in the database, functions
outputting a progress bar crash with a ZeroDivisionError.

SEE ALSO
========

oa-cache(1), oa-get(1)
