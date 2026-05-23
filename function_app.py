import importlib
import logging
import pkgutil

import azure.functions as func
from src import functions as functions_package

app = func.FunctionApp()
logger = logging.getLogger(__name__)


def _register_blueprints() -> None:
    for module_info in pkgutil.iter_modules(functions_package.__path__):
        module_name = f"{functions_package.__name__}.{module_info.name}"
        try:
            module = importlib.import_module(module_name)
            blueprint = getattr(module, "bp", None)
            if blueprint is not None:
                app.register_functions(blueprint)
                logger.info("Registered function blueprint: %s", module_name)
        except Exception as exc:
            logger.exception("Failed to register function blueprint %s: %s", module_name, exc)


_register_blueprints()
