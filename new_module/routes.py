# new_module/routes.py

from flask import Blueprint, render_template


new_module_bp = Blueprint('new_module', __name__, url_prefix='/new')

@new_module_bp.route('/example')
def example_route():
    return render_template('gps_show.html')




