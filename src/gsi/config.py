"""
Configuration for GSI from environment variables.
"""
import os
from src.utils.config import logger
from src.gsi.gsi_state import gsi_state


def load_gsi_config():
    """
    Load GSI configuration from environment variables.
    """
    # Get the GSI auth token from the environment
    gsi_auth_token = os.getenv('GSI_AUTH_TOKEN')

    # If not set, use a default value
    if not gsi_auth_token:
        logger.warning("GSI_AUTH_TOKEN environment variable not set. Using default value.")
        gsi_auth_token = "your_secret_token"
    else:
        logger.info("GSI_AUTH_TOKEN loaded from environment")

    # Set the auth token in the GSI state manager
    gsi_state.auth_token = gsi_auth_token

    return {
        "auth_token": gsi_auth_token
    }