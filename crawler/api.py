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

    def on_post(self, req, resp):
        logger.info('POST /summoner')
        body = json.loads(req.stream.read())

        # we dont check tls certificates so surpress the warning
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        config = client.ClientConfig(token=req.headers['X-RIOT-TOKEN'])
        routes = client.ClientRoutes(endpoint=req.headers['ENDPOINT'])
        riot_client = client.Client(config=config,
                                    routes=routes,
                                    )

        controller.post_summoner(riot_client=riot_client,
                                 summoner_name=body['summonerName'],
                                 game_range=(body['startIndex'], body['endIndex']) if body.get('startIndex') and body.get('endIndex') else None,
                                 )
        resp.status = falcon.HTTP_201


def create():
    api = falcon.API()
    api.add_route('/summoner', Summoner())
    logger.info('falcon initialized')

    conn = database.get_connection()
    database.kill_connection(conn)
    logger.info('database is ready')

    return api


application = create()
