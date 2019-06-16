IRC Commands
------------
Scrapes can be managed through IRC in #archivebot.

`module` is the name of the module (only snscrape is currently supported).

`target` is the username, hastag or search term for the query.

`maxpages` is currently only implemented for twitter-search and limits the pagnation to set (No pagnation by default).

`help` is redirects to this page.

`stop` if you're an admin forces the bot to stop immediately.

`update` if you're an admin forces the bot to close, complete a "git pull" for itself.

`version` gives the bot version.

`snsupdate` waits for all processes to complete, does a git pull for snscrape, repackage snscrape locally and then enable jobs.

Examples
________

`socialbot snscrape twitter-user ghostofapacket`

Searches for and grabs tweets from the twitter account `ghostofapacket`

`socialbot snscrape twitter-hashtag ghostofapacket`

Searches for and grabs tweets for the twitter hashtag `ghostofapacket`

`socialbot snscrape twitter-search ghostofapacket maxpages 1`

Searches twitter for the phrase `ghostofapacket` for `1` page

`socialbot snscrape instagram-user ghostofapacket`

Searches instagram for the user `ghostofapacket`

`socialbot snscrape instagram-hashtag ghostofpacket

Searches instagram for the hashtag `ghostofapacket`
