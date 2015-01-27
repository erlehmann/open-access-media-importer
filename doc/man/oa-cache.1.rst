========
oa-cache
========

-------------------------------------------
Open Access Media Importer cache operations
-------------------------------------------

:Author: Nils Dagsson Moskopp <nils@dieweltistgarnichtso.net>
:Date: 2015-01-27
:Manual section: 1

SYNOPSIS
========

oa-cache [--force-conversion] [--force-find] [-v] {clear-media |
    clear-database | convert-media | find-media | forget-converted |
    forget-downloaded | forget-uploaded | print-database-path | stats}
    [source]

oa-cache -h

DESCRIPTION
===========

oa-cache handles the metadata and media of resources indexed with the
Open Access Media Importer (OAMI), which are usually supplementary
materials of scientific papers. oa-cache can also print the OAMI
database path for a given source and and output media statistics.

No oa-cache sub-commands need internet access.

clear-media
    clear-media is used to delete media files downloaded by oa-get(1).

clear-database
    clear-database is used to delete the OAMI database for a given
    source. The OAMI database for a source contains the metadata of
    the media indexed with OAMI, plus their download, conversion and
    upload status.

convert-media
    convert-media is used to convert media files downloaded by
    oa-get(1) to royalty-free media formats. Currently, audio files
    are converted to Ogg Vorbis, whereas video files are converted to
    Ogg Theora+Vorbis.

find-media
    find-media is used to find media files suitable for conversion.

forget-converted
    forget-converted is used to make OAMI forget that it has converted
    media files belonging to a given source. Thus, during the next run
    of "oa-cache convert-media" all media files from that source might
    be converted again.

forget-downloaded
    forget-downloaded is used to make OAMI forget that it has
    downloaded media files belonging to a given source. Thus, during
    the next run of "oa-get download-media" all media files from that
    source might be downloaded again.

forget-uploaded
    forget-uploaded is used to make OAMI forget that it has uploaded
    media files belonging to a given source. Thus, during the next run
    of "oa-put upload-media" all media files from that source might be
    uploaded again.

print-database-path
    print-database-path is used to print the database path for a given
    source. This subcommand exists to interface to external tools like
    sqlitebrowser(1).

stats
    stats is used to print media statistics as a Python dictionary
    intended as input for the OAMI plot-helper script. The media
    statistics dictonary contains a count of free and non-free
    licenses ('licenses'), a count of how licensing was deduced
    ordered by publisher ('licensing_publishers'), a count of the
    internet media types for free and non-free materials and the
    misreported internet media types ('mimetypes'), a count of the
    internet media types prefix ("major type") for free and non-free
    materials by publisher ('mimetypes_prefix_publishers') and a count
    of the internet media types that were correctly or incorrectly
    assigned by publishers ('mimetypes_publishers'). Publishers are
    referenced by their DOI prefix.


OPTIONS
=======

--force-conversion
    Force conversion of supplementary materials already converted.
    This option is useless unless given with command "convert-media".

--force-find
    Force finding of supplementary materials already found.
    This option is useless unless given with command "find-media".

-h --help
    Show a short usage summary.

-v --verbose
    Increase verbosity. This option can be given multiple times.


BUGS
====

"print-database-path" returns bogus path when given bogus arguments.

When OAMI has no materials indexed in the database, functions
outputting a progress bar crash with a ZeroDivisionError.

SEE ALSO
========

oa-get(1), oa-put(1)
