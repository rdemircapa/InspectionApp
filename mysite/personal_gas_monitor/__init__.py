from flask import Blueprint

personal_gas_monitor_bp = Blueprint(
    'personal_gas_monitor',
    __name__,
    template_folder='templates'
)

from . import routes
