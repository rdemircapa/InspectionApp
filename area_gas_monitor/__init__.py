from flask import Blueprint

area_gas_monitor_bp = Blueprint('area_gas_monitor', __name__, template_folder='templates')


from . import routes  # ✅ En sonda olmalı
