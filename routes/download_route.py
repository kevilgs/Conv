from flask import Blueprint, send_file, flash, redirect, url_for
import os
from config import Config

download_bp = Blueprint('download', __name__)

@download_bp.route('/download/<filename>')
def download_file(filename):
    try:
        # Check multiple folders based on filename
        if filename.endswith('_final_report.xlsx'):
            # Final reports are in reports folder
            file_path = os.path.join(Config.REPORTS_FOLDER, filename)
        elif filename.endswith('_processed.xlsx'):
            # Intermediate files are in intermediate folder
            file_path = os.path.join(Config.INTERMEDIATE_FOLDER, filename)
        else:
            # Other files might be in uploads folder
            file_path = os.path.join(Config.UPLOAD_FOLDER, filename)
        
        # Debug output
        print(f"Looking for file: {filename}")
        print(f"File path: {file_path}")
        print(f"File exists: {os.path.exists(file_path)}")
        
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            # Try to find the file in any of the directories
            for folder in [Config.REPORTS_FOLDER, Config.INTERMEDIATE_FOLDER, Config.UPLOAD_FOLDER]:
                alt_path = os.path.join(folder, filename)
                if os.path.exists(alt_path):
                    print(f"Found file in alternative location: {alt_path}")
                    return send_file(alt_path, as_attachment=True)
            
            flash(f'File not found: {filename}')
            return redirect(url_for('upload.upload'))
            
    except Exception as e:
        flash(f'Error downloading file: {str(e)}')
        return redirect(url_for('upload.upload'))
