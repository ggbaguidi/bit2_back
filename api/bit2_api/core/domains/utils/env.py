import os

from bit2_api.core.domains.errors import ICoreException

NON_PROD_ENV_LIST = ["development", "staging", "stage-replica"]


class EnvironmentSetupError(ICoreException):
    """Exception raised when the environment is not set."""

    def __init__(self, env_name: str) -> None:
        self.message = f"Environment variable {env_name} is not set"
        self.http_code = 500
        self.key = "environmentError"
        super().__init__()


def get_env_variable(env_name: str, default: str = None) -> str:
    """
    Get an environment variable.
    Raise an EnvironmentSetupError if it is not set.
    """
    env = os.getenv(env_name)
    if env is None and default is None:
        raise EnvironmentSetupError(env_name)
    return env or default


def env_is_not_prod():
    """Check if the environment is not production."""
    current_env = get_env_variable("ENV_NAME")
    return current_env in NON_PROD_ENV_LIST
