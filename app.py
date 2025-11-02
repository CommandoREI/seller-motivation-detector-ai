from flask import Flask, request, jsonify, send_file, render_template_string
from flask_cors import CORS
import os
import json
from datetime import datetime
import subprocess
from ai_analyzer import EnhancedMotivationAnalyzer
from usage_tracker import UsageTracker
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import io

app = Flask(__name__)
CORS(app)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size

# Initialize enhanced analyzer
analyzer = EnhancedMotivationAnalyzer()

# Initialize usage tracker
usage_tracker = UsageTracker()

@app.route('/')
def index():
    """Serve the main application interface"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/analyze-transcript', methods=['POST'])
def analyze_transcript():
    """Analyze uploaded transcript for seller motivation"""
    try:
        data = request.get_json()
        transcript = data.get('transcript', '')
        
        if not transcript.strip():
            return jsonify({'error': 'No transcript provided'}), 400
        
        # Analyze the transcript using enhanced analyzer
        analysis = analyzer.analyze_transcript(transcript)
        
        return jsonify({
            'success': True,
            'analysis': analysis,
            'transcript': transcript,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        print(f"Error analyzing transcript: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analyze-audio', methods=['POST'])
def analyze_audio():
    """Analyze uploaded audio file for seller motivation"""
    try:
        # Get user ID from request (from WordPress or session)
        user_id = request.form.get('user_id', 'anonymous')
        
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        if audio_file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Save uploaded file temporarily
        filename = f"audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{audio_file.filename.split('.')[-1]}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        audio_file.save(filepath)
        
        try:
            # Get audio duration for usage tracking
            file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
            # Estimate duration: ~1MB per minute for typical audio
            estimated_duration_minutes = file_size_mb
            
            # Check usage limits before processing
            can_proceed, remaining = usage_tracker.check_audio_limit(user_id, estimated_duration_minutes)
            if not can_proceed:
                os.remove(filepath)
                return jsonify({
                    'error': f'Monthly audio limit exceeded. You have {remaining:.1f} minutes remaining this month. Limit: 500 minutes/month.',
                    'limit_exceeded': True,
                    'remaining_minutes': remaining
                }), 429
            
            # Check file size and compress if needed (Whisper has 25MB limit)
            MAX_FILE_SIZE_MB = 24  # Stay under 25MB limit with buffer
            if file_size_mb > MAX_FILE_SIZE_MB:
                # Compress audio file
                from pydub import AudioSegment
                compressed_filepath = filepath.replace(filename, f"compressed_{filename}").replace(filepath.split('.')[-1], 'mp3')
                
                # Load audio and export with lower bitrate
                audio = AudioSegment.from_file(filepath)
                # Calculate target bitrate to get under 25MB
                duration_seconds = len(audio) / 1000
                target_bitrate = int((MAX_FILE_SIZE_MB * 1024 * 8) / duration_seconds)  # kbps
                target_bitrate = min(target_bitrate, 64)  # Cap at 64kbps for quality
                
                audio.export(compressed_filepath, format="mp3", bitrate=f"{target_bitrate}k")
                
                # Remove original, use compressed
                os.remove(filepath)
                filepath = compressed_filepath
            
            # Transcribe audio using OpenAI Whisper API
            # Use the same client from analyzer that's already working
            with open(filepath, 'rb') as audio_data:
                transcription = analyzer.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_data,
                    response_format="verbose_json"
                )
            
            transcript = transcription.text
            actual_duration_minutes = transcription.duration / 60  # Convert seconds to minutes
            
            # Record actual usage
            usage_tracker.record_audio_usage(user_id, actual_duration_minutes)
            
            # Clean up uploaded file
            os.remove(filepath)
            
            # Analyze the transcript using enhanced analyzer
            analysis = analyzer.analyze_transcript(transcript)
            
            # Get updated usage stats
            usage_stats = usage_tracker.get_usage_stats(user_id)
            
            return jsonify({
                'success': True,
                'transcript': transcript,
                'analysis': analysis,
                'audio_duration_minutes': round(actual_duration_minutes, 2),
                'usage_stats': usage_stats,
                'timestamp': datetime.now().isoformat()
            })
        
        except Exception as e:
            if os.path.exists(filepath):
                os.remove(filepath)
            raise e
    
    except Exception as e:
        print(f"Error analyzing audio: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/usage-stats', methods=['GET'])
def get_usage_stats():
    """Get usage statistics for current user"""
    try:
        user_id = request.args.get('user_id', 'anonymous')
        stats = usage_tracker.get_usage_stats(user_id)
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/export-pdf', methods=['POST'])
def export_pdf():
    """Generate and download PDF report of analysis"""
    try:
        data = request.get_json()
        analysis = data.get('analysis', {})
        transcript = data.get('transcript', '')
        
        if not analysis:
            return jsonify({'error': 'No analysis data provided'}), 400
        
        # Create PDF in memory
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#3d5a4a'),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#3d5a4a'),
            spaceAfter=10,
            spaceBefore=15,
            fontName='Helvetica-Bold'
        )
        
        subheading_style = ParagraphStyle(
            'CustomSubHeading',
            parent=styles['Heading3'],
            fontSize=13,
            textColor=colors.HexColor('#5d7a68'),
            spaceAfter=8,
            spaceBefore=10,
            fontName='Helvetica-Bold'
        )
        
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['BodyText'],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#2d4a3a')
        )
        
        # Title
        story.append(Paragraph('Seller Motivation Analysis Report', title_style))
        story.append(Paragraph(f'Generated: {datetime.now().strftime("%B %d, %Y at %I:%M %p")}', body_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Motivation Score
        score_data = [[
            Paragraph('<b>Motivation Score</b>', heading_style),
            Paragraph(f'<b>{analysis.get("overall_score", "N/A")}/10</b>', heading_style)
        ], [
            Paragraph('Motivation Level', body_style),
            Paragraph(analysis.get('motivation_level', 'N/A'), body_style)
        ], [
            Paragraph('Confidence', body_style),
            Paragraph(f'{analysis.get("confidence", "N/A")}%', body_style)
        ]]
        
        score_table = Table(score_data, colWidths=[3*inch, 3*inch])
        score_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#5d7a68')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f0f5f0')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#c8d4c8')),
            ('PADDING', (0, 0), (-1, -1), 12),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(score_table)
        story.append(Spacer(1, 0.2*inch))
        
        # Deal Numbers Summary
        if 'deal_numbers' in analysis and analysis['deal_numbers'].get('fields_extracted', 0) > 0:
            story.append(Paragraph('Deal Numbers Summary', heading_style))
            deal_numbers = analysis['deal_numbers']
            extracted = deal_numbers.get('extracted', {})
            calculated = deal_numbers.get('calculated', {})
            
            deal_data = []
            
            # Financial Obligations
            if any([extracted.get('mortgage_balance'), extracted.get('arrears'), extracted.get('monthly_payment')]):
                deal_data.append([Paragraph('<b>Financial Obligations</b>', subheading_style), ''])
                if extracted.get('mortgage_balance'):
                    deal_data.append(['Mortgage Balance', f"${extracted['mortgage_balance']:,}"])
                if extracted.get('arrears'):
                    deal_data.append(['Arrears', f"${extracted['arrears']:,}"])
                if extracted.get('monthly_payment'):
                    deal_data.append(['Monthly Payment', f"${extracted['monthly_payment']:,}/mo"])
                if calculated.get('total_payoff'):
                    deal_data.append([Paragraph('<b>Total Payoff</b>', body_style), Paragraph(f"<b>${calculated['total_payoff']:,}</b>", body_style)])
            
            # Property Details
            if any([extracted.get('bedrooms'), extracted.get('bathrooms'), extracted.get('square_feet'), extracted.get('estimated_value')]):
                deal_data.append([Paragraph('<b>Property Details</b>', subheading_style), ''])
                if extracted.get('bedrooms'):
                    deal_data.append(['Bedrooms', str(extracted['bedrooms'])])
                if extracted.get('bathrooms'):
                    deal_data.append(['Bathrooms', str(extracted['bathrooms'])])
                if extracted.get('square_feet'):
                    deal_data.append(['Square Feet', f"{extracted['square_feet']:,} sq ft"])
                if extracted.get('estimated_value'):
                    deal_data.append(['Estimated Value', f"${extracted['estimated_value']:,}"])
            
            # Seller Requirements
            if extracted.get('seller_net_desired'):
                deal_data.append([Paragraph('<b>Seller Requirements</b>', subheading_style), ''])
                deal_data.append(['Net Proceeds Desired', f"${extracted['seller_net_desired']:,}"])
            
            # Quick Math
            if calculated.get('equity_available') is not None:
                deal_data.append([Paragraph('<b>Quick Math</b>', subheading_style), ''])
                if calculated.get('minimum_offer'):
                    deal_data.append(['Minimum Offer', f"${calculated['minimum_offer']:,}"])
                deal_data.append([Paragraph('<b>Equity Available</b>', body_style), Paragraph(f"<b>${calculated['equity_available']:,}</b>", body_style)])
            
            if deal_data:
                deal_table = Table(deal_data, colWidths=[3*inch, 3*inch])
                deal_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.white),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e8ede8')),
                    ('PADDING', (0, 0), (-1, -1), 10),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ]))
                story.append(deal_table)
                story.append(Spacer(1, 0.2*inch))
        
        # Key Insights
        if analysis.get('insights'):
            story.append(Paragraph('Key Insights', heading_style))
            for insight in analysis['insights']:
                story.append(Paragraph(f'• {insight}', body_style))
                story.append(Spacer(1, 0.1*inch))
            story.append(Spacer(1, 0.1*inch))
        
        # Timeline Urgency
        if analysis.get('timeline_urgency'):
            story.append(Paragraph('Timeline Urgency', heading_style))
            story.append(Paragraph(analysis['timeline_urgency'], body_style))
            story.append(Spacer(1, 0.2*inch))
        
        # Pain Points
        if analysis.get('pain_points'):
            story.append(Paragraph('Pain Points', heading_style))
            for point in analysis['pain_points']:
                story.append(Paragraph(f'• {point}', body_style))
                story.append(Spacer(1, 0.1*inch))
            story.append(Spacer(1, 0.1*inch))
        
        # Negotiation Strategy
        if analysis.get('negotiation_strategy'):
            story.append(Paragraph('Negotiation Strategy', heading_style))
            for strategy in analysis['negotiation_strategy']:
                story.append(Paragraph(f'• {strategy}', body_style))
                story.append(Spacer(1, 0.1*inch))
            story.append(Spacer(1, 0.1*inch))
        
        # Recommended Offer Approach
        if analysis.get('recommended_offer_approach'):
            story.append(Paragraph('Recommended Offer Approach', heading_style))
            offer = analysis['recommended_offer_approach']
            offer_data = []
            if offer.get('offer_range'):
                offer_data.append(['Offer Range', offer['offer_range']])
            if offer.get('closing_timeline'):
                offer_data.append(['Closing Timeline', offer['closing_timeline']])
            if offer.get('terms'):
                offer_data.append(['Terms', offer['terms']])
            if offer.get('presentation_style'):
                offer_data.append(['Presentation Style', offer['presentation_style']])
            
            if offer_data:
                offer_table = Table(offer_data, colWidths=[2*inch, 4*inch])
                offer_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0f8f0')),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#c8d4c8')),
                    ('PADDING', (0, 0), (-1, -1), 10),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ]))
                story.append(offer_table)
                story.append(Spacer(1, 0.2*inch))
        
        # Red Flags
        if analysis.get('red_flags'):
            story.append(Paragraph('Red Flags & Concerns', heading_style))
            for flag in analysis['red_flags']:
                story.append(Paragraph(f'⚠ {flag}', body_style))
                story.append(Spacer(1, 0.1*inch))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        # Generate filename
        filename = f"seller_motivation_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    
    except Exception as e:
        print(f"Error generating PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# HTML Template for the application
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Seller Motivation Detector AI - Real Estate Commando</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #5d7a68 0%, #3d5a4a 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #3d5a4a 0%, #2d4a3a 100%);
            color: white;
            padding: 50px 40px;
            text-align: center;
            border-bottom: 4px solid #8ba888;
        }
        
        .header h1 {
            font-size: 2.8rem;
            margin-bottom: 15px;
            font-weight: 700;
            letter-spacing: -0.5px;
        }
        
        .header p {
            font-size: 1.2rem;
            opacity: 0.95;
            max-width: 800px;
            margin: 0 auto;
            line-height: 1.6;
        }
        
        .header .tagline {
            font-size: 0.95rem;
            opacity: 0.8;
            margin-top: 10px;
            font-style: italic;
            color: #a8c5a3;
        }
        
        .main-content {
            padding: 50px;
            background: #f8f9fa;
        }
        
        .upload-section {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 40px;
        }
        
        .upload-card {
            border: 3px dashed #c8d4c8;
            border-radius: 12px;
            padding: 40px;
            text-align: center;
            transition: all 0.3s ease;
            cursor: pointer;
            background: white;
        }
        
        .upload-card:hover {
            border-color: #6ba86f;
            background: #f5faf5;
            transform: translateY(-3px);
            box-shadow: 0 8px 25px rgba(107, 168, 111, 0.15);
        }
        
        .upload-card.active {
            border-color: #5d7a68;
            background: #f0f5f0;
            border-style: solid;
        }
        
        .upload-icon {
            font-size: 3.5rem;
            margin-bottom: 20px;
            opacity: 0.8;
        }
        
        .upload-card h3 {
            font-size: 1.6rem;
            margin-bottom: 12px;
            color: #2d4a3a;
            font-weight: 600;
        }
        
        .upload-card p {
            color: #5a6c5a;
            margin-bottom: 25px;
            font-size: 1rem;
            line-height: 1.5;
        }
        
        .file-input {
            display: none;
        }
        
        .upload-btn {
            background: linear-gradient(135deg, #6ba86f 0%, #5d7a68 100%);
            color: white;
            border: none;
            padding: 14px 32px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1.05rem;
            transition: all 0.3s ease;
            font-weight: 600;
            box-shadow: 0 4px 12px rgba(93, 122, 104, 0.2);
        }
        
        .upload-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(93, 122, 104, 0.3);
            background: linear-gradient(135deg, #5d7a68 0%, #4d6a58 100%);
        }
        
        .transcript-area {
            width: 100%;
            min-height: 250px;
            padding: 20px;
            border: 2px solid #d4ddd4;
            border-radius: 8px;
            font-size: 0.95rem;
            font-family: 'Courier New', monospace;
            resize: vertical;
            background: #fafbfa;
            color: #2d4a3a;
            line-height: 1.6;
        }
        
        .transcript-area:focus {
            outline: none;
            border-color: #6ba86f;
            background: white;
        }
        
        .analyze-btn {
            width: 100%;
            background: linear-gradient(135deg, #5d7a68 0%, #3d5a4a 100%);
            color: white;
            border: none;
            padding: 20px;
            border-radius: 12px;
            cursor: pointer;
            font-size: 1.3rem;
            font-weight: 700;
            margin-top: 30px;
            transition: all 0.3s ease;
            box-shadow: 0 6px 20px rgba(61, 90, 74, 0.25);
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .analyze-btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 30px rgba(61, 90, 74, 0.35);
            background: linear-gradient(135deg, #4d6a58 0%, #2d4a3a 100%);
        }
        
        .analyze-btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .loading {
            text-align: center;
            padding: 40px;
            font-size: 1.2rem;
            color: #5d7a68;
            font-weight: 600;
        }
        
        .results {
            display: none;
            margin-top: 50px;
            animation: fadeIn 0.5s ease-in;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .score-card {
            background: linear-gradient(135deg, #5d7a68 0%, #3d5a4a 100%);
            color: white;
            padding: 50px;
            border-radius: 15px;
            text-align: center;
            margin-bottom: 40px;
            box-shadow: 0 10px 30px rgba(61, 90, 74, 0.3);
        }
        
        .score-number {
            font-size: 5.5rem;
            font-weight: 800;
            margin-bottom: 10px;
            text-shadow: 0 4px 10px rgba(0,0,0,0.2);
        }
        
        .score-level {
            font-size: 2rem;
            margin-bottom: 15px;
            font-weight: 600;
            opacity: 0.95;
        }
        
        .confidence {
            font-size: 1.2rem;
            opacity: 0.85;
            font-weight: 500;
        }
        
        .conversation-quality {
            background: #e8f5e9;
            border: 2px solid #6ba86f;
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 35px;
            display: flex;
            justify-content: space-around;
            align-items: center;
            flex-wrap: wrap;
            gap: 20px;
        }
        
        .quality-metric {
            text-align: center;
            min-width: 120px;
        }
        
        .quality-metric-value {
            font-size: 2rem;
            font-weight: 700;
            color: #3d5a4a;
            margin-bottom: 5px;
        }
        
        .quality-metric-label {
            font-size: 0.9rem;
            color: #5a6c5a;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .analysis-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 25px;
            margin-bottom: 40px;
        }
        
        .analysis-card {
            background: white;
            padding: 30px;
            border-radius: 12px;
            border-left: 5px solid #5d7a68;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .analysis-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.12);
        }
        
        .analysis-card h3 {
            color: #2d4a3a;
            margin-bottom: 20px;
            font-size: 1.4rem;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .indicator {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-right: 8px;
        }
        
        .indicator-positive {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .indicator-caution {
            background: #fff3cd;
            color: #856404;
            border: 1px solid #ffeaa7;
        }
        
        .indicator-negative {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        .indicator-info {
            background: #d1ecf1;
            color: #0c5460;
            border: 1px solid #bee5eb;
        }
        
        .analysis-card ul {
            list-style: none;
        }
        
        .analysis-card li {
            padding: 14px 0;
            border-bottom: 1px solid #e8ede8;
            line-height: 1.6;
            color: #3d5a4a;
            font-size: 0.95rem;
        }
        
        .analysis-card li:last-child {
            border-bottom: none;
        }
        
        .quote-section {
            background: #fffef5;
            padding: 35px;
            border-radius: 12px;
            margin-bottom: 35px;
            border: 2px solid #f0e68c;
            box-shadow: 0 4px 15px rgba(0,0,0,0.06);
        }
        
        .quote-section h3 {
            color: #2d4a3a;
            margin-bottom: 25px;
            font-size: 1.5rem;
            font-weight: 700;
        }
        
        .quote-card {
            background: white;
            padding: 20px 25px;
            border-left: 4px solid #d4a574;
            margin-bottom: 15px;
            border-radius: 6px;
            font-style: italic;
            color: #4a4a4a;
            line-height: 1.7;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }
        
        .offer-approach {
            background: linear-gradient(135deg, #e8f5e9 0%, #f0f8f0 100%);
            padding: 40px;
            border-radius: 15px;
            margin-bottom: 35px;
            border: 3px solid #6ba86f;
            box-shadow: 0 6px 20px rgba(107, 168, 111, 0.15);
        }
        
        .offer-approach h3 {
            color: #2d4a3a;
            margin-bottom: 30px;
            font-size: 1.6rem;
            font-weight: 700;
        }
        
        .offer-details {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 25px;
        }
        
        .offer-detail {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 3px 10px rgba(0,0,0,0.08);
            border-left: 4px solid #5d7a68;
        }
        
        .offer-detail-label {
            font-size: 0.85rem;
            color: #5a6c5a;
            margin-bottom: 8px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .offer-detail-value {
            font-size: 1.1rem;
            color: #2d4a3a;
            font-weight: 600;
            line-height: 1.5;
        }
        
        .red-flags-card {
            background: linear-gradient(135deg, #ffebee 0%, #fff5f5 100%);
            padding: 35px;
            border-radius: 12px;
            border: 3px solid #ef9a9a;
            box-shadow: 0 6px 20px rgba(239, 154, 154, 0.15);
        }
        
        .red-flags-card h3 {
            color: #c62828;
            margin-bottom: 25px;
            font-size: 1.5rem;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .red-flags-card ul {
            list-style: none;
        }
        
        .red-flags-card li {
            padding: 14px 0;
            border-bottom: 1px solid #ffcdd2;
            color: #c62828;
            font-weight: 500;
            line-height: 1.6;
        }
        
        .red-flags-card li:last-child {
            border-bottom: none;
        }
        
        @media (max-width: 768px) {
            .upload-section {
                grid-template-columns: 1fr;
            }
            
            .header h1 {
                font-size: 2rem;
            }
            
            .main-content {
                padding: 25px;
            }
            
            .score-number {
                font-size: 4rem;
            }
            
            .analysis-grid {
                grid-template-columns: 1fr;
            }
            
            .offer-details {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Seller Motivation Detector AI</h1>
            <p>Revolutionary AI-powered analysis of seller conversations and motivation</p>
            <p class="tagline">Powered by advanced natural language processing and psychological pattern recognition</p>
        </div>
        
        <div class="main-content">
            <!-- Usage Stats Display -->
            <div id="usageStatsBar" style="background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%); padding: 15px 25px; border-radius: 8px; margin-bottom: 30px; display: none; border-left: 4px solid #4caf50;">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
                    <div>
                        <strong style="color: #2e7d32; font-size: 1.1rem;">📊 Your Monthly Usage</strong>
                    </div>
                    <div style="display: flex; gap: 30px; flex-wrap: wrap;">
                        <div>
                            <span style="color: #5a6c5a; font-size: 0.9rem;">Audio Minutes:</span>
                            <strong id="audioMinutesUsed" style="color: #2e7d32; font-size: 1.1rem; margin-left: 8px;">0</strong>
                            <span style="color: #7a8a7a; font-size: 0.9rem;"> / 500</span>
                        </div>
                        <div>
                            <span style="color: #5a6c5a; font-size: 0.9rem;">Remaining:</span>
                            <strong id="audioMinutesRemaining" style="color: #2e7d32; font-size: 1.1rem; margin-left: 8px;">500</strong>
                            <span style="color: #7a8a7a; font-size: 0.9rem;"> minutes</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="upload-section">
                <div class="upload-card" id="audioCard">
                    <div class="upload-icon">🎙️</div>
                    <h3>Upload Audio File</h3>
                    <p>Upload a recorded conversation (MP3, WAV, M4A)</p>
                    <input type="file" id="audioFile" class="file-input" accept=".mp3,.wav,.m4a,.flac,.ogg">
                    <button class="upload-btn" onclick="document.getElementById('audioFile').click()">Choose Audio File</button>
                </div>
                
                <div class="upload-card active" id="transcriptCard">
                    <div class="upload-icon">📝</div>
                    <h3>Paste Transcript</h3>
                    <p>Type or paste the conversation transcript</p>
                    <textarea id="transcriptText" class="transcript-area" placeholder="Paste your conversation transcript here...

Example format:
Seller: Hi, I need to sell my house quickly due to a job relocation.
Agent: Tell me about your timeline and situation.
Seller: We need to close within 30 days if possible. The house needs some work but we're flexible on price for a quick sale."></textarea>
                </div>
            </div>
            
            <button class="analyze-btn" id="analyzeBtn" onclick="analyzeMotivation()">▶ Analyze Seller Motivation</button>
            
            <div id="loading" class="loading" style="display: none;">
                Analyzing conversation with AI...
            </div>
            
            <div id="results" class="results">
                <div class="score-card">
                    <div class="score-number" id="scoreNumber">0</div>
                    <div class="score-level" id="scoreLevel">Motivation Level</div>
                    <div class="confidence" id="confidence">Confidence</div>
                    <button onclick="exportPDF()" style="margin-top: 25px; background: white; color: #3d5a4a; border: 2px solid white; padding: 14px 35px; border-radius: 8px; cursor: pointer; font-size: 1.05rem; font-weight: 700; transition: all 0.3s ease; box-shadow: 0 4px 12px rgba(0,0,0,0.2);" onmouseover="this.style.background='#f0f5f0'; this.style.transform='translateY(-2px)';" onmouseout="this.style.background='white'; this.style.transform='translateY(0)';">📄 Download PDF Report</button>
                </div>
                
                <div class="conversation-quality" id="conversationQuality">
                    <div class="quality-metric">
                        <div class="quality-metric-value" id="qualityLevel">-</div>
                        <div class="quality-metric-label">Quality</div>
                    </div>
                    <div class="quality-metric">
                        <div class="quality-metric-value" id="wordCount">-</div>
                        <div class="quality-metric-label">Words</div>
                    </div>
                    <div class="quality-metric">
                        <div class="quality-metric-value" id="exchangeCount">-</div>
                        <div class="quality-metric-label">Exchanges</div>
                    </div>
                </div>
                
                <!-- Deal Numbers Summary Section -->
                <div id="dealNumbersSection" style="display: none; margin: 30px 0;">
                    <div style="background: linear-gradient(135deg, #e8f5e9 0%, #f0f8f0 100%); border: 3px solid #6ba86f; border-radius: 15px; padding: 40px; box-shadow: 0 8px 20px rgba(107, 168, 111, 0.15);">
                        <h3 style="color: #2d4a3a; font-size: 1.8rem; margin-bottom: 30px; font-weight: 700;">
                            Deal Numbers Summary
                        </h3>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px;">
                            <!-- Financial Obligations -->
                            <div style="background: white; padding: 28px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); border-left: 5px solid #1976d2;">
                                <h4 style="color: #1976d2; margin-bottom: 20px; font-size: 1.2rem; font-weight: 700;">
                                    Financial Obligations
                                </h4>
                                <div id="financialObligations" style="font-size: 0.95rem; line-height: 1.9;"></div>
                            </div>
                            
                            <!-- Property Details -->
                            <div style="background: white; padding: 28px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); border-left: 5px solid #f57c00;">
                                <h4 style="color: #f57c00; margin-bottom: 20px; font-size: 1.2rem; font-weight: 700;">
                                    Property Details
                                </h4>
                                <div id="propertyDetails" style="font-size: 0.95rem; line-height: 1.9;"></div>
                            </div>
                            
                            <!-- Seller Requirements -->
                            <div style="background: white; padding: 28px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); border-left: 5px solid #7b1fa2;">
                                <h4 style="color: #7b1fa2; margin-bottom: 20px; font-size: 1.2rem; font-weight: 700;">
                                    Seller Requirements
                                </h4>
                                <div id="sellerRequirements" style="font-size: 0.95rem; line-height: 1.9;"></div>
                            </div>
                            
                            <!-- Quick Math -->
                            <div style="background: white; padding: 28px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); border-left: 5px solid #2e7d32;">
                                <h4 style="color: #2e7d32; margin-bottom: 20px; font-size: 1.2rem; font-weight: 700;">
                                    Quick Math
                                </h4>
                                <div id="quickMath" style="font-size: 0.95rem; line-height: 1.9;"></div>
                            </div>
                        </div>
                        <div id="extractionConfidence" style="margin-top: 25px; padding: 18px; background: rgba(107, 168, 111, 0.15); border-radius: 10px; text-align: center; font-weight: 700; color: #2d4a3a; font-size: 1.05rem;"></div>
                    </div>
                </div>
                
                <div class="analysis-grid">
                    <div class="analysis-card">
                        <h3>Key Insights</h3>
                        <ul id="insights"></ul>
                    </div>
                    
                    <div class="analysis-card">
                        <h3>Negotiation Strategy</h3>
                        <ul id="strategy"></ul>
                    </div>
                    
                    <div class="analysis-card">
                        <h3>Timeline Urgency</h3>
                        <p id="timeline" style="padding: 15px 0; font-size: 1.1rem; color: #2d4a3a; font-weight: 600;"></p>
                    </div>
                    
                    <div class="analysis-card">
                        <h3>Pain Points</h3>
                        <ul id="painPoints"></ul>
                    </div>
                    
                    <div class="analysis-card">
                        <h3>Emotional Analysis</h3>
                        <ul id="emotions"></ul>
                    </div>
                </div>
                
                <div class="quote-section">
                    <h3>Key Quotes from Conversation</h3>
                    <div id="quotes"></div>
                </div>
                
                <div class="offer-approach">
                    <h3>Recommended Offer Approach</h3>
                    <div class="offer-details" id="offerApproach"></div>
                </div>
                
                <div class="red-flags-card" id="redFlagsCard" style="display: none;">
                    <h3><span class="indicator indicator-negative">WARNING</span> Red Flags & Concerns</h3>
                    <ul id="redFlags"></ul>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let currentAnalysis = null;
        
        // Handle file selection
        document.getElementById('audioFile').addEventListener('change', function(e) {
            if (e.target.files.length > 0) {
                const file = e.target.files[0];
                const fileName = file.name;
                const fileSize = (file.size / (1024 * 1024)).toFixed(2); // MB
                
                // Show filename on the button
                const audioCard = document.getElementById('audioCard');
                audioCard.classList.add('active');
                document.getElementById('transcriptCard').classList.remove('active');
                
                // Update button text to show selected file
                const btn = audioCard.querySelector('.upload-btn');
                btn.textContent = `✓ ${fileName} (${fileSize} MB)`;
                btn.style.background = 'linear-gradient(135deg, #4caf50 0%, #45a049 100%)';
            }
        });
        
        // Handle transcript input
        document.getElementById('transcriptText').addEventListener('input', function(e) {
            if (e.target.value.trim()) {
                document.getElementById('transcriptCard').classList.add('active');
                document.getElementById('audioCard').classList.remove('active');
            }
        });
        
        // Load and display usage stats on page load
        async function loadUsageStats() {
            try {
                const userId = getUserId();
                const response = await fetch(`/api/usage-stats?user_id=${userId}`);
                const data = await response.json();
                
                if (data.success) {
                    updateUsageDisplay(data.stats);
                }
            } catch (error) {
                console.error('Error loading usage stats:', error);
            }
        }
        
        function getUserId() {
            // Try to get user ID from WordPress or use anonymous
            return window.wpUserId || 'anonymous';
        }
        
        function updateUsageDisplay(stats) {
            document.getElementById('usageStatsBar').style.display = 'block';
            document.getElementById('audioMinutesUsed').textContent = Math.round(stats.audio_minutes_used);
            document.getElementById('audioMinutesRemaining').textContent = Math.round(stats.audio_minutes_remaining);
            
            // Change color if running low
            const remaining = stats.audio_minutes_remaining;
            const usageBar = document.getElementById('usageStatsBar');
            if (remaining < 50) {
                usageBar.style.background = 'linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%)';
                usageBar.style.borderLeftColor = '#ff9800';
            } else if (remaining < 100) {
                usageBar.style.background = 'linear-gradient(135deg, #fff9c4 0%, #fff59d 100%)';
                usageBar.style.borderLeftColor = '#ffc107';
            }
        }
        
        async function analyzeMotivation() {
            const audioFile = document.getElementById('audioFile').files[0];
            const transcript = document.getElementById('transcriptText').value.trim();
            
            if (!audioFile && !transcript) {
                alert('Please upload an audio file or paste a transcript');
                return;
            }
            
            // Show loading
            document.getElementById('loading').style.display = 'block';
            document.getElementById('results').style.display = 'none';
            document.getElementById('analyzeBtn').disabled = true;
            
            try {
                let response;
                const userId = getUserId();
                
                if (audioFile) {
                    // Upload and analyze audio
                    const formData = new FormData();
                    formData.append('audio', audioFile);
                    formData.append('user_id', userId);
                    
                    response = await fetch('/api/analyze-audio', {
                        method: 'POST',
                        body: formData
                    });
                } else {
                    // Analyze transcript
                    response = await fetch('/api/analyze-transcript', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ transcript })
                    });
                }
                
                const data = await response.json();
                
                if (response.status === 429) {
                    // Usage limit exceeded
                    alert(data.error || 'Monthly usage limit exceeded. Please try again next month.');
                    return;
                }
                
                if (data.success) {
                    displayResults(data.analysis, data.transcript);
                    
                    // Update usage stats if returned
                    if (data.usage_stats) {
                        updateUsageDisplay(data.usage_stats);
                    }
                    
                    // Show audio duration if available
                    if (data.audio_duration_minutes) {
                        const durationMsg = `Audio transcribed: ${data.audio_duration_minutes.toFixed(1)} minutes`;
                        console.log(durationMsg);
                    }
                } else {
                    alert('Error: ' + (data.error || 'Unknown error occurred'));
                }
            } catch (error) {
                console.error('Error:', error);
                alert('Error analyzing conversation: ' + error.message);
            } finally {
                document.getElementById('loading').style.display = 'none';
                document.getElementById('analyzeBtn').disabled = false;
            }
        }
        
        // Load usage stats when page loads
        document.addEventListener('DOMContentLoaded', loadUsageStats);
        
        function displayResults(analysis, transcript) {
            currentAnalysis = analysis;
            
            // Update score card
            document.getElementById('scoreNumber').textContent = analysis.overall_score;
            document.getElementById('scoreLevel').textContent = analysis.motivation_level + ' Motivation';
            document.getElementById('confidence').textContent = `${analysis.confidence}% Confidence`;
            
            // Update conversation quality
            const convQuality = analysis.conversation_quality || {};
            document.getElementById('qualityLevel').textContent = convQuality.quality || 'N/A';
            document.getElementById('wordCount').textContent = convQuality.word_count || 0;
            document.getElementById('exchangeCount').textContent = convQuality.exchange_count || 0;
            
            // Update insights with indicators
            const insightsList = document.getElementById('insights');
            insightsList.innerHTML = '';
            (analysis.insights || []).forEach(insight => {
                const li = document.createElement('li');
                const indicator = getInsightIndicator(insight);
                li.innerHTML = indicator + insight;
                insightsList.appendChild(li);
            });
            
            // Update strategy
            const strategyList = document.getElementById('strategy');
            strategyList.innerHTML = '';
            (analysis.negotiation_strategy || []).forEach(strategy => {
                const li = document.createElement('li');
                li.textContent = strategy;
                strategyList.appendChild(li);
            });
            
            // Update timeline with indicator
            const timelineText = analysis.timeline_urgency || 'Not specified';
            const timelineIndicator = getTimelineIndicator(timelineText);
            document.getElementById('timeline').innerHTML = timelineIndicator + timelineText;
            
            // Update pain points
            const painPointsList = document.getElementById('painPoints');
            painPointsList.innerHTML = '';
            (analysis.pain_points || []).forEach(point => {
                const li = document.createElement('li');
                li.textContent = point;
                painPointsList.appendChild(li);
            });
            
            // Update emotions
            const emotionsList = document.getElementById('emotions');
            emotionsList.innerHTML = '';
            const emotionAnalysis = analysis.emotion_analysis || {};
            const li1 = document.createElement('li');
            li1.textContent = `Dominant Emotion: ${emotionAnalysis.dominant_emotion || 'neutral'}`;
            emotionsList.appendChild(li1);
            const li2 = document.createElement('li');
            li2.textContent = `Emotional Intensity: ${emotionAnalysis.emotional_intensity || 0}/10`;
            emotionsList.appendChild(li2);
            const li3 = document.createElement('li');
            li3.textContent = `Emotional State: ${emotionAnalysis.emotional_stability || 'stable'}`;
            emotionsList.appendChild(li3);
            
            // Update quotes
            const quotesDiv = document.getElementById('quotes');
            quotesDiv.innerHTML = '';
            if (analysis.key_quotes && analysis.key_quotes.length > 0) {
                analysis.key_quotes.forEach(quote => {
                    const quoteCard = document.createElement('div');
                    quoteCard.className = 'quote-card';
                    quoteCard.textContent = `"${quote}"`;
                    quotesDiv.appendChild(quoteCard);
                });
            } else {
                quotesDiv.innerHTML = '<p style="padding: 20px; text-align: center; color: #666;">No significant quotes identified</p>';
            }
            
            // Update offer approach
            const offerApproach = analysis.recommended_offer_approach || {};
            const offerDiv = document.getElementById('offerApproach');
            offerDiv.innerHTML = '';
            
            const offerFields = [
                { label: 'Offer Range', value: offerApproach.offer_range },
                { label: 'Closing Timeline', value: offerApproach.closing_timeline },
                { label: 'Terms', value: offerApproach.terms },
                { label: 'Presentation Style', value: offerApproach.presentation_style },
                { label: 'Follow-up', value: offerApproach.follow_up }
            ];
            
            offerFields.forEach(field => {
                const detailDiv = document.createElement('div');
                detailDiv.className = 'offer-detail';
                detailDiv.innerHTML = `
                    <div class="offer-detail-label">${field.label}</div>
                    <div class="offer-detail-value">${field.value || 'N/A'}</div>
                `;
                offerDiv.appendChild(detailDiv);
            });
            
            // Update red flags
            const redFlagsList = document.getElementById('redFlags');
            const redFlagsCard = document.getElementById('redFlagsCard');
            redFlagsList.innerHTML = '';
            
            if (analysis.red_flags && analysis.red_flags.length > 0) {
                analysis.red_flags.forEach(flag => {
                    const li = document.createElement('li');
                    li.textContent = flag;
                    redFlagsList.appendChild(li);
                });
                redFlagsCard.style.display = 'block';
            } else {
                redFlagsCard.style.display = 'none';
            }
            
            // Display deal numbers if available
            if (analysis.deal_numbers && analysis.deal_numbers.fields_extracted > 0) {
                const dealNumbers = analysis.deal_numbers;
                const extracted = dealNumbers.extracted || {};
                const calculated = dealNumbers.calculated || {};
                
                // Financial Obligations
                const financialHtml = [];
                if (extracted.mortgage_balance) financialHtml.push(`<div style="margin: 8px 0;"><strong>Mortgage Balance:</strong> $${extracted.mortgage_balance.toLocaleString()}</div>`);
                if (extracted.arrears) financialHtml.push(`<div style="margin: 8px 0;"><strong>Arrears:</strong> $${extracted.arrears.toLocaleString()}</div>`);
                if (extracted.months_behind) financialHtml.push(`<div style="margin: 8px 0;"><strong>Months Behind:</strong> ${extracted.months_behind} months</div>`);
                if (extracted.monthly_payment) financialHtml.push(`<div style="margin: 8px 0;"><strong>Monthly Payment:</strong> $${extracted.monthly_payment.toLocaleString()}/mo</div>`);
                if (calculated.total_payoff) financialHtml.push(`<div style="margin: 18px 0 0 0; padding: 14px; background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%); border-radius: 8px; font-weight: bold; color: #2e7d32;"><strong>Total Payoff:</strong> $${calculated.total_payoff.toLocaleString()}</div>`);
                document.getElementById('financialObligations').innerHTML = financialHtml.length > 0 ? financialHtml.join('') : '<div style="color: #999;">No financial data extracted</div>';
                
                // Property Details
                const propertyHtml = [];
                if (extracted.bedrooms) propertyHtml.push(`<div style="margin: 8px 0;"><strong>Bedrooms:</strong> ${extracted.bedrooms}</div>`);
                if (extracted.bathrooms) propertyHtml.push(`<div style="margin: 8px 0;"><strong>Bathrooms:</strong> ${extracted.bathrooms}</div>`);
                if (extracted.square_feet) propertyHtml.push(`<div style="margin: 8px 0;"><strong>Square Feet:</strong> ${extracted.square_feet.toLocaleString()} sq ft</div>`);
                if (extracted.estimated_value) propertyHtml.push(`<div style="margin: 8px 0;"><strong>Estimated Value:</strong> $${extracted.estimated_value.toLocaleString()}</div>`);
                if (extracted.repair_costs) propertyHtml.push(`<div style="margin: 8px 0;"><strong>Repair Costs:</strong> $${extracted.repair_costs.toLocaleString()}</div>`);
                document.getElementById('propertyDetails').innerHTML = propertyHtml.length > 0 ? propertyHtml.join('') : '<div style="color: #999;">No property data extracted</div>';
                
                // Seller Requirements
                const sellerHtml = [];
                if (extracted.seller_net_desired) sellerHtml.push(`<div style="margin: 8px 0;"><strong>Net Proceeds Desired:</strong> $${extracted.seller_net_desired.toLocaleString()}</div>`);
                if (extracted.asking_price) sellerHtml.push(`<div style="margin: 8px 0;"><strong>Asking Price:</strong> $${extracted.asking_price.toLocaleString()}</div>`);
                if (extracted.days_until_foreclosure) sellerHtml.push(`<div style="margin: 8px 0;"><strong>Days Until Foreclosure:</strong> ${extracted.days_until_foreclosure}</div>`);
                if (extracted.additional_notes) sellerHtml.push(`<div style="margin: 18px 0 0 0; padding: 14px; background: #f5f5f5; border-radius: 8px; font-size: 0.9rem; line-height: 1.7;"><strong>Notes:</strong> ${extracted.additional_notes}</div>`);
                document.getElementById('sellerRequirements').innerHTML = sellerHtml.length > 0 ? sellerHtml.join('') : '<div style="color: #999;">No seller requirements extracted</div>';
                
                // Quick Math
                const mathHtml = [];
                if (calculated.total_payoff) mathHtml.push(`<div style="margin: 8px 0;"><strong>Total Payoff:</strong> $${calculated.total_payoff.toLocaleString()}</div>`);
                if (calculated.minimum_offer) mathHtml.push(`<div style="margin: 8px 0;"><strong>Minimum Offer:</strong> $${calculated.minimum_offer.toLocaleString()}</div>`);
                if (calculated.equity_available) {
                    const equityColor = calculated.equity_available > 0 ? '#2e7d32' : '#c62828';
                    mathHtml.push(`<div style="margin: 18px 0 0 0; padding: 14px; background: linear-gradient(135deg, ${calculated.equity_available > 0 ? '#e8f5e9' : '#ffebee'} 0%, ${calculated.equity_available > 0 ? '#c8e6c9' : '#ffcdd2'} 100%); border-radius: 8px; font-weight: bold; color: ${equityColor};"><strong>Equity Available:</strong> $${calculated.equity_available.toLocaleString()}</div>`);
                }
                document.getElementById('quickMath').innerHTML = mathHtml.length > 0 ? mathHtml.join('') : '<div style="color: #999;">Insufficient data for calculations</div>';
                
                // Extraction confidence
                document.getElementById('extractionConfidence').textContent = `Extraction Confidence: ${dealNumbers.confidence}% (${dealNumbers.fields_extracted} fields extracted)`;
                
                // Show the deal numbers section
                document.getElementById('dealNumbersSection').style.display = 'block';
            } else {
                document.getElementById('dealNumbersSection').style.display = 'none';
            }
            
            // Show results and scroll
            document.getElementById('results').style.display = 'block';
            document.getElementById('results').scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
        
        function getInsightIndicator(insight) {
            const lowerInsight = insight.toLowerCase();
            if (lowerInsight.includes('financial distress') || lowerInsight.includes('foreclosure')) {
                return '<span class="indicator indicator-positive">OPPORTUNITY</span> ';
            } else if (lowerInsight.includes('divorce') || lowerInsight.includes('urgent')) {
                return '<span class="indicator indicator-caution">URGENT</span> ';
            } else if (lowerInsight.includes('strong motivation') || lowerInsight.includes('good opportunity')) {
                return '<span class="indicator indicator-positive">OPPORTUNITY</span> ';
            } else if (lowerInsight.includes('ai analysis')) {
                return '<span class="indicator indicator-info">INSIGHT</span> ';
            }
            return '';
        }
        
        function getTimelineIndicator(timeline) {
            const lowerTimeline = timeline.toLowerCase();
            if (lowerTimeline.includes('critical') || lowerTimeline.includes('immediate')) {
                return '<span class="indicator indicator-negative">CRITICAL</span> ';
            } else if (lowerTimeline.includes('high')) {
                return '<span class="indicator indicator-caution">HIGH</span> ';
            } else if (lowerTimeline.includes('moderate')) {
                return '<span class="indicator indicator-info">MODERATE</span> ';
            } else if (lowerTimeline.includes('low')) {
                return '<span class="indicator indicator-positive">LOW</span> ';
            }
            return '';
        }
        
        async function exportPDF() {
            if (!currentAnalysis) {
                alert('No analysis data available to export');
                return;
            }
            
            try {
                const response = await fetch('/api/export-pdf', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        analysis: currentAnalysis,
                        transcript: document.getElementById('transcriptText').value
                    })
                });
                
                if (response.ok) {
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `seller_motivation_analysis_${new Date().getTime()}.pdf`;
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                } else {
                    const error = await response.json();
                    alert('Error generating PDF: ' + (error.error || 'Unknown error'));
                }
            } catch (error) {
                console.error('Error exporting PDF:', error);
                alert('Error generating PDF: ' + error.message);
            }
        }
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5004))
    app.run(host='0.0.0.0', port=port, debug=True)
