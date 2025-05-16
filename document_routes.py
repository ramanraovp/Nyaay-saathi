import os
import json
from datetime import datetime
from flask import request, jsonify, make_response
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from legal_data import DOCUMENT_TEMPLATES, LEGAL_TIMELINES

def handle_get_document_templates():
    templates = list(DOCUMENT_TEMPLATES.keys())
    return jsonify({"templates": templates})

# Handle my specific document template API request
def handle_get_document_template_endpoint(template_id):
    if template_id in DOCUMENT_TEMPLATES:
        return jsonify(DOCUMENT_TEMPLATES[template_id])
    else:
        return jsonify({"error": "Template not found"}), 404

# Handle my document generation API request
def handle_generate_document():
    data = request.json
    template_id = data.get('template_id')
    fields = data.get('fields', {})
    
    if template_id not in DOCUMENT_TEMPLATES:
        return jsonify({"error": "Template not found"}), 404
    
    # Add the current date if not provided
    if 'current_date' not in fields:
        fields['current_date'] = datetime.now().strftime("%d/%m/%Y")
    
    # Fill the template with provided fields
    template = DOCUMENT_TEMPLATES[template_id]['template']
    for key, value in fields.items():
        placeholder = "{" + key + "}"
        template = template.replace(placeholder, value)
    
    return jsonify({
        "title": DOCUMENT_TEMPLATES[template_id]['title'],
        "document": template
    })

# Handle PDF generation API request
def handle_generate_document_pdf():
    data = request.json
    template_id = data.get('template_id')
    fields = data.get('fields', {})
    
    if template_id not in DOCUMENT_TEMPLATES:
        return jsonify({"error": "Template not found"}), 404
    
    # Add current date 
    if 'current_date' not in fields:
        fields['current_date'] = datetime.now().strftime("%d/%m/%Y")
    
    # Fill template with provided fields
    template = DOCUMENT_TEMPLATES[template_id]['template']
    for key, value in fields.items():
        placeholder = "{" + key + "}"
        template = template.replace(placeholder, value)
    
    title = DOCUMENT_TEMPLATES[template_id]['title']
    
    try:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter,
                                rightMargin=72, leftMargin=72,
                                topMargin=72, bottomMargin=72)
        
        styles = getSampleStyleSheet()
        style_title = styles['Heading1']
        style_title.alignment = 1  # Center
        
        style_normal = styles['Normal']
        style_normal.fontSize = 11
        style_normal.leading = 14
        
        # I am trying to create paragraphs for each bot reply
        elements = []
        elements.append(Paragraph(title, style_title))
        elements.append(Spacer(1, 18))
        

        lines = template.split('\n')
        for line in lines:
            if line.strip():  
                elements.append(Paragraph(line, style_normal))
            else:
                elements.append(Spacer(1, 12))  
        
    
        doc.build(elements)
        
        pdf_data = buffer.getvalue()
        buffer.close()
        
        # Prepare my response
        response = make_response(pdf_data)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename="{title.replace(" ", "_")}.pdf"'
        
        return response
    except Exception as e:
        print(f"PDF Generation Error: {str(e)}")
        return jsonify({"error": "Failed to generate PDF"}), 500

# Handle the  legal timeline API request when I click onto legal timeleines
def handle_get_legal_timeline_endpoint(timeline_id):
    if timeline_id in LEGAL_TIMELINES:
        return jsonify({"timeline": LEGAL_TIMELINES[timeline_id]})
    else:
        return jsonify({"error": "Timeline not found"}), 404

def register_document_routes(app):
    # Document template routes
    app.add_url_rule('/api/document_templates', view_func=handle_get_document_templates, methods=['GET'])
    
    def get_document_template(template_id):
        return handle_get_document_template_endpoint(template_id)
    
    def get_legal_timeline(timeline_id):
        return handle_get_legal_timeline_endpoint(timeline_id)
    
    app.add_url_rule('/api/document_template/<template_id>', view_func=get_document_template, methods=['GET'])
    app.add_url_rule('/api/generate_document', view_func=handle_generate_document, methods=['POST'])
    app.add_url_rule('/api/generate_document_pdf', view_func=handle_generate_document_pdf, methods=['POST'])
    app.add_url_rule('/api/legal_timeline/<timeline_id>', view_func=get_legal_timeline, methods=['GET'])