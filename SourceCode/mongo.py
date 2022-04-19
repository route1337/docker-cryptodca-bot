#!/usr/bin/env python3
"""Functions to use with MongoDB"""
#
# Python Script:: mongo.py
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

import datetime
import logging
import pymongo


def set_last_buy_date(bot_name: str, db_server: str):
    """Sets the date the last time the currency was bought

    Args:
    bot_name: The name of the bot
    db_server: The MongoDB server to connect to
    """
    timestamp = datetime.datetime.utcnow()
    try:
        # Create a Mongo client to connect to
        mongo_client = pymongo.MongoClient(db_server)
        bot_db = mongo_client[bot_name]
        buy_date = bot_db["buy-date"]
    except Exception as err:
        logging.error("Can't connect to buy-date collection: %s", err)
    try:
        buy_date.find_one_and_update({"_id": 1},
                                     {"$set": {"time": timestamp}}, upsert=True)
    except Exception as err:
        logging.error("Can't update buy date record: %s", err)


def check_last_buy_date(bot_name: str, db_server: str,
                        cool_down_period: int) -> bool:
    """Get the date of the last time the currency was bought
    and returns true if it >= cool down period

    Args:
    bot_name: The name of the bot
    db_server: The MongoDB server to connect to
    cool_down_period: The time period in days that you will wait before transacting

    Returns:
    clear_to_buy: A bool that is true if we are clear to buy
    """
    try:
        # Create a Mongo client to connect to
        mongo_client = pymongo.MongoClient(db_server)
        bot_db = mongo_client[bot_name]
        buy_date = bot_db["buy-date"]
    except Exception as err:
        logging.error("Can't connect to buy-date collection: %s", err)
    # Create an initial record if the record doesn't exist yet
    #if buy_date.find({'_id': 1}).count() == 0:
    if buy_date.count_documents({'_id': 1}, limit=1) == 0:
        logging.info("Initializing new last buy date")
        timestamp = datetime.datetime.utcnow()
        buy_date.find_one_and_update({"_id": 1},
                                     {"$set": {"time": timestamp}}, upsert=True)
        return False
    try:
        last_buy_date = buy_date.find_one({"_id": 1})['time']
    except Exception as err:
        logging.error("Can't get buy date record: %s", err)
        return False
    time_difference = datetime.datetime.utcnow() - last_buy_date
    return time_difference.days >= cool_down_period
