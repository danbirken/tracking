import datetime
import json
import logging
import time

class Tracker(object):
    @classmethod
    def get_tracker(cls, backend_uri, request_parser=None, logger=None):
        if backend_uri == 'console':
            return ConsoleTracker(request_parser, logger)

        if backend_uri.startswith('mongodb://'):
            return MongoTracker(request_parser, logger, backend_uri)

    def __init__(self, request_parser, logger):
        self.request_parser = request_parser
        self.logger = logger

    def _record(self, event):
        raise NotImplementedError()

    def _log_tracking_error(self, error):
        if self.logger is not None:
            self.logger.error(error)
        
    def track_event(self, name, info=None):
        try:
            event_info = {}

            if info is not None:
                event_info.update(info)

            event_info['name'] = name
            event_info['time'] = time.time()
            event_info['ctime'] = datetime.datetime.now().ctime()
            self._record(event_info)
        except Exception, e:
            self._log_tracking_error('Exception in track_event: %s' % e)

    def track_view(self, request, info=None):
        try:
            if self.request_parser is None:
                self.logger.error('Can\'t track pageview events unless request_parser is set.')
                return

            event_info = {}

            event_info['request'] = self.request_parser.get_info_from_request(request)

            if info is not None:
                event_info.update(info)
            
            self.track_event(
                'view',
                event_info
            )
        except Exception, e:
            self._log_tracking_error('Exception in track_event: %s' % e)

class ConsoleTracker(Tracker):
    def _record(self, event):
        print json.dumps(event)

class MongoTracker(Tracker):
    def __init__(self, request_parser, logger, mongo_uri):
        super(MongoTracker, self).__init__(request_parser, logger)
        import pymongo
        client = pymongo.MongoClient(mongo_uri)
        self.events_collection = client[mongo_uri.rsplit('/')[-1]].events

    def _record(self, event):
        self.events_collection.insert(event)

class RequestParser(object):
    def get_info_from_request(self, request):
        raise NotImplementedError()

class WerkzeugRequestParser(object):
    def get_info_from_request(self, request):
        return {
            'host': request.host,
            'secure': request.is_secure,
            'method': request.method,
            'path': request.path,
            'query_string': request.query_string,
            'remote_addr': request.remote_addr,
            'url': request.url,
            'referrer': request.referrer,
            'user_agent': {
                'full': request.user_agent.string,
                'platform': request.user_agent.platform,
                'browser': request.user_agent.browser,
                'version': request.user_agent.version,
                'language': request.user_agent.language,
            }
        }
