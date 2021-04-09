import json
import urllib3

import falcon

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
        logger.info('crawling')
        body = json.loads(req.stream.read())

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

        controller.post_summoner(
            riot_client=riot_client,
            summoner_name=body['summonerName'],
        )
        resp.status = falcon.HTTP_201


def create():
    api = falcon.API()
    api.add_route('/', Summoner())
    logger.info('falcon initialized')

    conn = database.get_connection()
    database.kill_connection(conn)
    logger.info('database is ready')

    return api


application = create()
