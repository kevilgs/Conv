from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
import os
import json
from werkzeug.utils import secure_filename
from config import Config

upload_bp = Blueprint('upload', __name__)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

@upload_bp.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
            file.save(filepath)
            flash('File uploaded successfully!')
            
            # Redirect to classification management page
            return redirect(url_for('upload.manage_classifications', filename=filename))
        else:
            flash('Please upload a CSV file only')
    
    return render_template('upload.html')

@upload_bp.route('/manage-classifications/<filename>')
def manage_classifications(filename):
    """Show classification management page after upload"""
    file_path = os.path.join(Config.UPLOAD_FOLDER, filename)
    if not os.path.exists(file_path):
        flash('File not found')
        return redirect(url_for('upload.upload'))
    
    return render_template('manage_classifications.html', filename=filename)
