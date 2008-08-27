"""
Live statistics extension
"""
from datetime import datetime
from pydispatch import dispatcher
from scrapy.core import signals
from scrapy.core.engine import scrapyengine
from scrapy.management.web import banner

class SpiderStats(object):
    def __init__(self):
        self.scraped = 0
        self.crawled = 0
        self.started = None
        self.finished = None

class LiveStats(object):
    webconsole_id = 'livestats'
    webconsole_name = 'Spider live statistics of current run'

    def __init__(self):
        self.domains = {}
        dispatcher.connect(self.domain_open, signal=signals.domain_open)
        dispatcher.connect(self.domain_closed, signal=signals.domain_closed)
        dispatcher.connect(self.item_scraped, signal=signals.item_scraped)
        dispatcher.connect(self.response_downloaded, signal=signals.response_downloaded)

        from scrapy.management.web import webconsole_discover_module
        dispatcher.connect(self.webconsole_discover_module, signal=webconsole_discover_module)

    def domain_open(self, domain, spider):
        pstats = SpiderStats()
        self.domains[spider.domain_name] = pstats
        pstats.started = datetime.now()
        pstats.finished = None

    def domain_closed(self, domain, spider):
        self.domains[spider.domain_name].finished = datetime.now()

    def item_scraped(self, item, spider):
        self.domains[spider.domain_name].scraped += 1

    def response_downloaded(self, response, spider):
        #sometimes we download responses without opening/closing domains,
        #for example from scrapy shell
        if self.domains.get(spider.domain_name):
            self.domains[spider.domain_name].crawled += 1
            
    def webconsole_render(self, wc_request):
        sch = scrapyengine.scheduler
        dwl = scrapyengine.downloader

        totdomains = totscraped = totcrawled = totscheduled = totactive = totpending = 0
        s = banner(self)
        s += "<table border='1'>\n"
        s += "<tr><th>Domain</th><th>Items<br>Scraped</th><th>Pages<br>Crawled</th><th>Scheduler<br>Pending</th><th>Downloader<br/>Pending</th><th>Downloader<br/>Active</th><th>Start time</th><th>Finish time</th><th>Run time</th></tr>\n"
        for d in sorted(self.domains.keys()):
            scheduled = len(sch.pending_requests[d]) if d in sch.pending_requests else 0
            active, pending = len(dwl.active_requests(d)), len(dwl.request_queue(d))
            stats = self.domains[d]
            runtime = stats.finished - stats.started if stats.finished else datetime.now() - stats.started

            s += '<tr><td>%s</td><td align="right">%d</td><td align="right">%d</td><td align="right">%d</td><td align="right">%d</td><td align="right">%d</td><td>%s</td><td>%s</td><td>%s</td></tr>\n' % \
                 (d, stats.scraped, stats.crawled, scheduled, pending, active, str(stats.started), str(stats.finished), str(runtime))

            totdomains += 1
            totscraped += stats.scraped
            totcrawled += stats.crawled
            totscheduled += scheduled
            totactive += active
            totpending += pending
        s += '<tr><td><b>%d domains</b></td><td align="right"><b>%d</b></td><td align="right"><b>%d</b></td><td align="right"><b>%d</b></td><td align="right"><b>%d</b></td><td align="right"><b>%d</b></td><td/><td/></tr>\n' % \
             (totdomains, totscraped, totcrawled, totscheduled, totactive, totpending)
        s += "</table>\n"

        s += "</body>\n"
        s += "</html>\n"

        return s

    def webconsole_discover_module(self):
        return self
