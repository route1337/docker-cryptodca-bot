#!/usr/bin/env python3
"""A bot that attempts to buy cryptocurrency using a DCA method."""
#
# Python Script:: cryptodca_bot.py
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

import logging
import argparse
import bot_internals


def main(config_file: str, debug_mode: bool):
    """
    The main function that triggers and runs the bot functions

    Args:
    config_file: Path to the JSON file containing credentials and config options
    debug_mode: Use Sandbox APIs instead of production
    """
    # Configure logging
    logging.basicConfig(level=logging.INFO,
                        datefmt='%m/%d/%G %H:%M:%S', format='%(asctime)s %(message)s')
    # Load the configuration file
    config_params = bot_internals.read_bot_config(config_file)
    # Start the correct cycle
    if config_params[4]:
        bot_internals.gemini_exchange_cycle(config_file, debug_mode)
    else:
        bot_internals.coinbase_pro_cycle(config_file, debug_mode)


if __name__ == '__main__':
    # This function parses and return arguments passed in
    # Assign description to the help doc
    PARSER = argparse.ArgumentParser(
        description='A bot that attempts to buy cryptocurrency using a DCA method.')
    # Add arguments
    PARSER.add_argument(
        '-c', '--configFile', type=str, help="Path to config.json file", required=True
    )
    PARSER.add_argument(
        '-d', '--debug', help="Use sandbox APIs", required=False, action='store_true'
    )
    # Array for all arguments passed to script
    ARGS = PARSER.parse_args()
    ARG_CONFIG = ARGS.configFile
    ARG_DEBUG = ARGS.debug
    main(ARG_CONFIG, ARG_DEBUG)
