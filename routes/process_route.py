from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
import json
from services.csv_processor import CSVProcessor
from services.xlsx_generator import XLSXGenerator
from services.final_report_generator import FinalReportGenerator
from services.report_data_processor import ReportDataProcessor
import pandas as pd
import os

process_bp = Blueprint('process', __name__)

@process_bp.route('/generate_intermediate/<filename>', methods=['POST'])
def generate_intermediate(filename):
    try:
        # Handle custom classifications if provided
        custom_classifications = {}
        custom_classifications_json = request.form.get('custom_classifications', '{}')
        if custom_classifications_json:
            try:
                custom_classifications = json.loads(custom_classifications_json)
            except json.JSONDecodeError:
                custom_classifications = {}
        
        # Process CSV with custom classifications
        processor = CSVProcessor()
        
        # Add custom classifications to processor and save to CSV if provided
        if custom_classifications:
            processor.wagon_classifier.add_custom_classifications(custom_classifications)
            flash(f'Added {len(custom_classifications)} custom classifications and saved to CSV file')
        
        processed_df = processor.process_csv(filename)
        
        # Generate intermediate XLSX
        xlsx_generator = XLSXGenerator()
        xlsx_filename = xlsx_generator.generate_intermediate_xlsx(processed_df, filename)
        
        # Check if intermediate file was created successfully
        if not os.path.exists(xlsx_filename):
            flash(f'Error: Intermediate file was not created')
            return redirect(url_for('upload.upload'))
            
        # Redirect to the wait page where user can edit the Excel file natively
        just_filename = os.path.basename(xlsx_filename)
        return render_template('edit_intermediate.html', 
                               original_filename=filename,
                               intermediate_filename=just_filename, 
                               full_path=xlsx_filename)
                               
    except Exception as e:
        flash(f'Error processing file: {str(e)}')
        return redirect(url_for('upload.upload'))

@process_bp.route('/generate_final/<original_filename>/<intermediate_filename>', methods=['POST'])
def generate_final(original_filename, intermediate_filename):
    try:
        from config import Config
        xlsx_filename = os.path.join(Config.INTERMEDIATE_FOLDER, intermediate_filename)
        
        # Generate final report
        final_report_generator = FinalReportGenerator()
        
        # Read the intermediate XLSX file with full path
        try:
            intermediate_df = pd.read_excel(xlsx_filename)
        except FileNotFoundError:
            flash(f'Error: Cannot find intermediate file: {xlsx_filename}')
            return redirect(url_for('upload.upload'))
        
        # Process the data to get handedover and takenover data
        report_processor = ReportDataProcessor()
        handedover_data = report_processor.process_handedover_data(intermediate_df)
        takenover_data = report_processor.process_takenover_data(intermediate_df)
        
        # Generate final report with all required arguments
        final_report_filename, message = final_report_generator.generate_final_report(
            handedover_data, 
            takenover_data, 
            intermediate_filename  # Use intermediate filename to preserve date/timestamp
        )
        
        # Check if generation was successful
        if final_report_filename:
            # extract just the filename
            just_filename = os.path.basename(final_report_filename)
            return redirect(url_for('download.download_file', filename=just_filename))
        else:
            flash(f'Error generating final report: {message}')
            return redirect(url_for('upload.upload'))
            
    except Exception as e:
        flash(f'Error processing final report: {str(e)}')
        return redirect(url_for('upload.upload'))
