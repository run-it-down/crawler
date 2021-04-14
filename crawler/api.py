import json
import threading
import urllib3

import falcon
import psutil

import client
import controller
try:
    import database
    import util
except ModuleNotFoundError:
    print('common package not in python path')


logger = util.Logger(__name__)


class Summoner:
    def on_get(self, req, resp):
        logger.info('checking if summoner exists')
        params = req.params
        if "summoner" not in params:
            resp.status = falcon.HTTP_BAD_REQUEST
        else:
            summoner = controller.summoner_exists(params["summoner"])
            if summoner is None:
                resp.status = falcon.HTTP_NOT_FOUND
            else:
                resp.status = falcon.HTTP_OK

    def on_post(self, req, resp):
        body = json.loads(req.stream.read())
        logger.info(f'crawling "{body["summonerName"]}"')

        # we dont check tls certificates so surpress the warning
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        config = client.ClientConfig(
            token=req.headers['X-RIOT-TOKEN'],
        )
        routes = client.ClientRoutes(
            endpoint=req.headers['ENDPOINT'],
        )
        riot_client = client.Client(
            config=config,
            routes=routes,
        )

        t = threading.Thread(
            target=controller.crawl_summoner,
            args=(riot_client, body['summonerName']),
        )
        t.start()
        resp.status_code = falcon.HTTP_201


class Status:

    def on_get(self, req, resp):
        cpu = psutil.cpu_percent()
        data = '{"cpu": ' + str(cpu) + '}'
        resp.text = data
        resp.status = falcon.HTTP_OK


def create():
    api = falcon.App()
    api.add_route('/', Summoner())
    api.add_route('/status', Status())
    logger.info('falcon initialized')

    conn = database.get_connection()
    database.kill_connection(conn)
    logger.info('database is ready')

    return api


application = create()
