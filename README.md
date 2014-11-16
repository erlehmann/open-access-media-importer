<h1>Open Access Media Importer</h1>
<p>The aim of this project is to write a tool that would:
<ul>
<li>regularly spider PubMed Central to locate audio and video files published in the supplementary materials of CC BY-licensed articles in the Open subset
<li>convert these files to OGG
<li>upload them to Wikimedia Commons, along with the respective metadata
<li>provide for easy extension to other CC-BY sources, beyond PubMed Central
<li>(possibly) suggest Wikipedia articles for which the video might be relevant
</ul>
<p><a href="http://en.wikiversity.org/wiki/User:OpenScientist/Open_grant_writing/Wissenswert_2011">Open Grant Writing for Open Access Media Importer</a>
<p><a href="http://chrismaloney.org/notes/OAMI">Notes on the Open Access Media Importer by Chris Maloney</a>
<p>A screencast showing usage can be played back with <kbd>ttyplay screencast</kbd>.
<h2>Configuration</h2>
<p>Copy the <code>userconfig.example</code> file to <code>$HOME/config/open-access-media-importer/userconfig</code>, uncomment the lines beginning with <code># username</code> and <code># password</code> and fill in your username and password for <i>Wikimedia Commons</i>.
<h2>Import of supplementary materials by DOI</h2>
<ol>
<li>Look up the DOIs of one or more open access articles.
<li>Pipe the DOIs to <code>oami_pmc_doi_import</code>, e.g. <kbd>echo 10.1371/journal.pcbi.0030212 | oami_pmc_doi_import</kbd>.
</ol>
<h2>Import of supplementary materials by PMCID</h2>
<ol>
<li>Look up the PMCIDs of one or more open access articles.
<li>Pipe the PMCIDs to <code>oami_pmc_pmcid_import</code>, e.g. <kbd>echo PMC3751716 | oami_pmc_pmcid_import</kbd>.
</ol>
<p>You can fetch PMCIDs for articles with <code>oa-pmc-ids</code>; try <kbd>oa-pmc-ids --help</kbd>.
<h2>Dependencies</h2>
<ul>
<li>python-dateutil <http://pypi.python.org/pypi/python-dateutil>
<li>python-elixir <http://elixir.ematia.de/trac/wiki>
<li>python-gi
<li>gir1.2-gstreamer-1.0
<li>gir1.2-gst-plugins-base-1.0
<li>gstreamer1.0-plugins-good
<li>gstreamer1.0-plugins-ugly
<li>gstreamer1.0-plugins-bad
<li>gstreamer1.0-libav
<li>python-magic <http://www.darwinsys.com/file/>
<li>python-mutagen <http://code.google.com/p/mutagen/>
<li>python-progressbar <http://pypi.python.org/pypi/progressbar/2.2>
<li>python-xdg <http://freedesktop.org/wiki/Software/pyxdg>
<li>python-werkzeug <http://werkzeug.pocoo.org/>
<li>python-wikitools <http://code.google.com/p/python-wikitools/> (python-wikitools was imported into our tree and patched to ease deployment)
</ul>
<p>To plot mimetypes occurring in sources, install python-matplotlib and pipe the output of <kbd>oa-cache stats $SOURCE</kbd> to <code>plot-helper</code>, where <code>$SOURCE</code> is either <code>pmc</code>, <code>pmc_doi</code> or <code>pmc_pmcid</code>.
<h2>License</h2>
<p>The Open Access Media Importer is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License  as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
