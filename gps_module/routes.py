# gps_module/routes.py
from flask import Blueprint, render_template

gps_bp = Blueprint('gps', __name__, url_prefix='/gps')

@gps_bp.route('/show')
def show_gps():
    return render_template('gps_show.html')
