import snscrape
class IRC(threading.Thread):
    def __init__(self):
        settings.logger.log('snscrape - Starting scrape for ' + irc.scrapesite)
