# crawler
Client for Riot API

## Usage
POST `https://crawler.run-it-down.lol/summoner`

Headers
```yaml
X-Riot-Token: "RGAPI-XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"
endpoint: "https://euw1.api.riotgames.com/"
```

Body
```yaml
summonerName: "Zeekay",
startIndex: 5,
endIndex: 7
```
