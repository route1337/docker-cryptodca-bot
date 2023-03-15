Crypto DCA Bot
==============
This bot is designed to buy cryptocurrency on Coinbase Pro or Gemini ActiveTrader using a USD prefunded portfolio on a regular basis.
(AKA Dollar Cost Averaging)

Docker -> GHCR
--------------
Route 1337 LLC is moving to ghcr.io and away from Docker Hub.  
This does mean that anything in the `route1337` namespace on Docker Hub should no longer be trusted, as it could be run by an attacker paying for the namespace.

USE AT YOUR OWN RISK
--------------------
The primary authors of this bot run it full time against their personal Coinbase Pro and Gemini accounts,
however we make no warranties that the bot will function. It could crash and miss a buy, or it could buy
the wrong amount. So far it has done well for us, but your mileage may vary.  
As with any open source code: **USE THIS BOT AT YOUR OWN RISK!**

Why not use the built-in Exchange functions?
--------------------------------------------
Both Coinbase and Gemini charge much higher fees for their automated DCA functions, than you can get just buying it by hand in their pro
interfaces. This is a waste of money when buying small amounts daily, vs large buys. Using a bot to take advantage of the APIs for the Coinbase Pro or Gemini ActiveTrader
interfaces will allow you to get the lower fee tiers while still making small DCA buys without spending too much on fees.  
The savings from this homegrown DCA will add up quickly, especially if you are doing $10-$20 daily buys.

Running The Bot
---------------
To run the bot you will need Docker and docker-compose installed on your computer. Along with your configuration as laid out below.  

    docker-compose up -d

Choosing An Exchange
--------------------
If you specify Gemini credentials at all in the `config.json` file then the bot will use Gemini even if Coinbase Pro
credentials are also specified.

Config File
-----------
You will need the following:

1. Coinbase Pro or Gemini credentials tied to the portfolio you want to run the bot against
2. DCA logic parameters:
    1. The cryptocurrency you want to transact in. (It must support being paired against USD)
    2. The buy amount you want in $USD.

The following sections are optional.

1. Time variables in the bot config
   1. Period of days between buys (Default: 1)
2. AWS credentials:
   1. AWS API keys
   2. SNS topic ARN (us-east-1 only for now)
3. Optionally you can override the bot name

These settings should be in a configuration file named `config.json` and placed in `./config`.
Additionally, you can override the volume mount to a new path if you prefer.
The file should look like this:

```json
{
  "bot": {
    "currency": "ETH",
    "buy_amount": 20.00,
     "cost_average_period": 3,
     "name": "Test-Bot"
  },
  "coinbase": {
    "api_key": "YOUR_API_KEY",
    "api_secret": "YOUR_API_SECRET",
    "passphrase": "YOUR_API_PASSPHRASE"
  },
   "gemini": {
    "api_key": "YOUR_API_KEY",
    "api_secret": "YOUR_API_SECRET"
   },
   "aws": {
    "access_key": "YOUR_API_KEY",
    "secret_access_key": "YOUR_API_SECRET",
    "sns_arn": "arn:aws:sns:us-east-1:012345678901:dca_alerts"
  }
}
```

Running outside of Docker
-------------------------
You can run the bot outside of Docker pretty easily.

```bash
python SourceCode/cryptodca-bot.py -c /path/to/config.json
```

Note: It assumes a specific hostname for MongoDB that you will need to adjust in the code to do this.

Logs
----
The bot will log activity to stdout, so you can review it with `docker logs`

Donate To Support This Bot
--------------------------
Route 1337 LLC's open source code heavily relies on donations. If you find this bot useful, please consider using the GitHub Sponsors button to show your continued support.

Thank you for your support!
