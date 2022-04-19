#!/usr/bin/env python3
"""Internal functions the bot uses"""
#
# Python Script:: bot_internals.py
#
# Linter:: pylint
#
# Copyright 2022, Route 1337 LLC, All Rights Reserved.
#
# Maintainers:
# - Matthew Ahrenstein: @ahrenstein
#
# See LICENSE
#

from itertools import count
import json
import logging
import time
import boto3
import coinbase_pro
import gemini_exchange
import mongo


# Hard coded variables
#CYCLE_MINUTES = 60
CYCLE_MINUTES = 1 #TODO change this back after testing


def read_bot_config(config_file: str) -> [str, float, int, bool, bool, str]:
    """Open a JSON file and get the bot configuration
    Args:
        config_file: Path to the JSON file containing credentials and config options

    Returns:
        crypto_currency: The cryptocurrency that will be monitored
        buy_amount: The price in $USD that will be purchased each period
        cost_average_period: The time period in days for the buy frequency
        aws_loaded: A bool to determine if AWS configuration options exist
        using_gemini: A bool to determine if the bot should use Gemini
        bot-name: The name of the bot
    """
    with open(config_file) as creds_file:
        data = json.load(creds_file)
    crypto_currency = data['bot']['currency']
    buy_amount = data['bot']['buy_amount']
    aws_loaded = bool('aws' in data)
    using_gemini = bool('gemini' in data)
    if 'cost_average_period' in data['bot']:
        cost_average_period = data['bot']['cost_average_period']
    else:
        cost_average_period = 1
    if 'name' in data['bot']:
        bot_name = data['bot']['name']
    else:
        if using_gemini:
            bot_name = "Gemini-" + crypto_currency + "-bot"
        else:
            bot_name = "CoinbasePro-" + crypto_currency + "-bot"
    return crypto_currency, buy_amount, cost_average_period, aws_loaded, using_gemini, bot_name


def get_aws_creds_from_file(config_file: str) -> [str, str, str]:
    """Open a JSON file and get AWS credentials out of it
    Args:
        config_file: Path to the JSON file containing credentials

    Returns:
        aws_access_key: The AWS access key your bot will use
        aws_secret_key: The AWS secret access key
        sns_topic_arn: The SNS topic ARN to publish to
    """
    with open(config_file) as creds_file:
        data = json.load(creds_file)
    aws_access_key = data['aws']['access_key']
    aws_secret_key = data['aws']['secret_access_key']
    sns_topic_arn = data['aws']['sns_arn']
    return aws_access_key, aws_secret_key, sns_topic_arn


def post_to_sns(aws_access_key: str, aws_secret_key: str, sns_topic_arn: str,
                message_subject: str, message_body: str):
    """Post a message and subject to AWS SNS

    Args:
    aws_access_key: The AWS access key your bot will use
    aws_secret_key: The AWS secret access key
    sns_topic_arn: The SNS topic ARN to publish to
    message_subject: A message subject to post to SNS
    message_body: A message body to post to SNS
    """
    sns = boto3.client('sns', region_name="us-east-1",
                       aws_access_key_id=aws_access_key, aws_secret_access_key=aws_secret_key)
    sns.publish(TopicArn=sns_topic_arn, Subject=message_subject, Message=message_body)


def gemini_exchange_cycle(config_file: str, debug_mode: bool) -> None:
    """Perform bot cycles using Gemini as the exchange

        Args:
        config_file: Path to the JSON file containing credentials
        debug_mode: Are we running in debugging mode?
        """
    # Load the configuration file
    config_params = read_bot_config(config_file)
    if config_params[3]:
        aws_config = get_aws_creds_from_file(config_file)
        message = f"{config_params[5]} has been started"
        post_to_sns(aws_config[0], aws_config[1], aws_config[2], message, message)
    # Set API URLs
    if debug_mode:
        gemini_exchange_api_url = "https://api.sandbox.gemini.com"
        mongo_db_connection = "mongodb://bots:dollarcostaverage@bots-db:27017/"
    else:
        gemini_exchange_api_url = "https://api.gemini.com"
        mongo_db_connection = "mongodb://bots:dollarcostaverage@bots-db:27017/"
    logging.info("Starting bot...")
    logging.info("DCAing %s on Gemini ActiverTrader to buy $%s worth every %s day(s)",
                 config_params[0], config_params[1], config_params[2])
    for cycle in count():
        logging.info("Cycle %s", cycle)
        coin_current_price = gemini_exchange.get_coin_price(
            gemini_exchange_api_url, config_params[0])
        if coin_current_price == -1:
            message = f"Coin price invalid for {config_params[0]}." \
                      f" This could be an API issue. Ending cycle"
            logging.error(message)
            subject = f"{config_params[5]} price invalid for {config_params[0]}"
            if config_params[5]:
                post_to_sns(aws_config[0], aws_config[1], aws_config[2],
                            subject, message)
            time.sleep(CYCLE_MINUTES * 60)
            continue
        # Verify that there is enough money to transact, otherwise don't bother
        if not gemini_exchange.verify_balance(gemini_exchange_api_url,
                                              config_file, config_params[1]):
            message = f"Not enough account balance to buy" \
                      f" ${config_params[1]} worth of {config_params[0]}"
            subject = f"{config_params[5]} Funding Issue"
            if config_params[5]:
                post_to_sns(aws_config[0], aws_config[1], aws_config[2],
                            subject, message)
            logging.warning("%s", message)
            # Sleep for the specified cycle interval then end the cycle
            time.sleep(CYCLE_MINUTES * 60)
            continue
        # Check if the cost_average_period has passed
        clear_to_proceed = mongo.check_last_buy_date(config_params[5], mongo_db_connection,
                                                     config_params[2])
        if clear_to_proceed is True:
            logging.info("Last buy date outside cost averaging period.")
            logging.info("The current price of %s is %s.", config_params[0], coin_current_price)
            did_buy = gemini_exchange.buy_currency(gemini_exchange_api_url,
                                                   config_file,
                                                   config_params[0], config_params[1])
            message = f"Buy success status is {did_buy} for" \
                      f" ${config_params[1]} worth of {config_params[0]}"
            subject = f"{config_params[5]} Buy Status Alert"
            mongo.set_last_buy_date(config_params[5], mongo_db_connection)
            logging.info("%s", message)
            if config_params[3]:
                post_to_sns(aws_config[0], aws_config[1], aws_config[2],
                            subject, message)
        else:
            logging.info("Last buy date inside cool down period. No buys will be attempted.")

        # Sleep for the specified cycle interval
        time.sleep(CYCLE_MINUTES * 60)


def coinbase_pro_cycle(config_file: str, debug_mode: bool) -> None:
    """Perform bot cycles using Coinbase Pro as the exchange

        Args:
        config_file: Path to the JSON file containing credentials
        debug_mode: Are we running in debugging mode?
        """
    # Load the configuration file
    config_params = read_bot_config(config_file)
    if config_params[3]:
        aws_config = get_aws_creds_from_file(config_file)
        message = f"{config_params[5]} has been started"
        post_to_sns(aws_config[0], aws_config[1], aws_config[2], message, message)
        logging.info("AWS configuration detected and loaded")
    # Set API URLs
    if debug_mode:
        coinbase_pro_api_url = "https://api-public.sandbox.exchange.coinbase.com/"
        mongo_db_connection = "mongodb://bots:dollarcostaverage@bots-db:27017/"
    else:
        coinbase_pro_api_url = "https://api.exchange.coinbase.com/"
        mongo_db_connection = "mongodb://bots:dollarcostaverage@bots-db:27017/"
    logging.info("Starting bot...")
    logging.info("DCAing %s on Coinbase Pro to buy $%s worth every %s day(s)",
                 config_params[0], config_params[1], config_params[2])
    for cycle in count():
        logging.info("Cycle %s", cycle)
        # Verify that there is enough money to transact, otherwise don't bother
        if not coinbase_pro.verify_balance(coinbase_pro_api_url, config_file, config_params[1]):
            message = f"Not enough account balance to buy" \
                      f" ${config_params[1]} worth of {config_params[0]}"
            subject = f"{config_params[5]} Funding Issue"
            if config_params[5]:
                post_to_sns(aws_config[0], aws_config[1], aws_config[2],
                            subject, message)
            logging.warning("%s", message)
            # Sleep for the specified cycle interval then end the cycle
            time.sleep(CYCLE_MINUTES * 60)
            continue
        # Get the coin current price
        coin_current_price = coinbase_pro.get_coin_price \
            (coinbase_pro_api_url, config_file, config_params[0])
        # Check if the cost_average_period has passed
        clear_to_proceed = mongo.check_last_buy_date(config_params[5], mongo_db_connection,
                                                     config_params[2])
        if clear_to_proceed is True:
            logging.info("Last buy date outside cost averaging period.")
            logging.info("The current price of %s is %s.", config_params[0], coin_current_price)
            did_buy = coinbase_pro.buy_currency(coinbase_pro_api_url,
                                                config_file, config_params[0], config_params[1])
            message = f"Buy success status is {did_buy} for" \
                      f" ${config_params[1]} worth of {config_params[0]}"
            subject = f"{config_params[5]} Buy Status Alert"
            mongo.set_last_buy_date(config_params[5], mongo_db_connection)
            logging.info("%s", message)
            if config_params[3]:
                post_to_sns(aws_config[0], aws_config[1], aws_config[2],
                            subject, message)
        else:
            logging.info("Last buy date inside cool down period. No buys will be attempted.")

        # Sleep for the specified cycle interval
        time.sleep(CYCLE_MINUTES * 60)
