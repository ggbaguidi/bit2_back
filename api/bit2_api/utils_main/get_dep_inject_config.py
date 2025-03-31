"""This file contains the function that will be used by the dependency"""
from bit2_api.core.use_cases import ExtractGameResult


# pylint: disable=invalid-name
def get_dependencies_injection_config(
    DatabaseClient,
    GameResultRepository,
    for_testing: bool = False,
):
    """
    This function returns a function that will be used by the dependency
    injection library to configure the dependencies injection.
    """

    def configure_dependencies_injection(binder):
        """
        Configure dependencies injections
        """

        use_case_bindings = [
            # Game result use cases
            {
                "use_cases": [ExtractGameResult],
                "providers": [
                    GameResultRepository,
                    DatabaseClient,
                ],
            },
        ]

        for use_case_binding in use_case_bindings:
            for use_case in use_case_binding["use_cases"]:
                # If we are in testing mode, we don't want to instantiate the providers
                # as they are already created in fixtures with memory data.
                if for_testing:
                    binder.bind(
                        use_case,
                        use_case(*list(use_case_binding["providers"])),
                    )
                # Otherwise, we instantiate the providers -> ... provider() for ...
                else:
                    binder.bind(
                        use_case,
                        use_case(
                            *[provider() for provider in use_case_binding["providers"]]
                        ),
                    )

    return configure_dependencies_injection
