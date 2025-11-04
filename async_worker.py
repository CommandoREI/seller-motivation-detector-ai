"""
Async worker for processing audio files in background
"""
import os
import threading
from datetime import datetime
from job_queue import job_queue

def process_audio_async(job_id, filepath, user_id, analyzer, usage_tracker, app_config):
    """
    Process audio file asynchronously in background thread
    
    Args:
        job_id: Unique job identifier
        filepath: Path to uploaded audio file
        user_id: User identifier
        analyzer: EnhancedMotivationAnalyzer instance
        usage_tracker: UsageTracker instance
        app_config: Flask app config dict
    """
    try:
        # Update job status to processing
        job_queue.update_job(job_id, status='processing', progress=10, 
                            message='Checking file size and preparing audio...')
        
        # Get file size
        file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
        
        # Check if compression needed
        MAX_FILE_SIZE_MB = 24  # Stay under 25MB limit with buffer
        if file_size_mb > MAX_FILE_SIZE_MB:
            job_queue.update_job(job_id, progress=20, 
                                message='Compressing audio file...')
            
            from pydub import AudioSegment
            filename = os.path.basename(filepath)
            compressed_filepath = filepath.replace(filename, f"compressed_{filename}").replace(filepath.split('.')[-1], 'mp3')
            
            # Load audio and export with lower bitrate
            audio = AudioSegment.from_file(filepath)
            duration_seconds = len(audio) / 1000
            target_bitrate = int((MAX_FILE_SIZE_MB * 1024 * 8) / duration_seconds)
            target_bitrate = min(target_bitrate, 64)
            
            audio.export(compressed_filepath, format="mp3", bitrate=f"{target_bitrate}k")
            
            # Remove original, use compressed
            os.remove(filepath)
            filepath = compressed_filepath
        
        # Transcribe audio
        job_queue.update_job(job_id, progress=30, 
                            message='Transcribing audio with AI... This may take 1-2 minutes.')
        
        with open(filepath, 'rb') as audio_data:
            transcription = analyzer.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_data,
                response_format="verbose_json"
            )
        
        transcript = transcription.text
        actual_duration_minutes = transcription.duration / 60
        
        # Record usage
        usage_tracker.record_audio_usage(user_id, actual_duration_minutes)
        
        # Clean up audio file
        if os.path.exists(filepath):
            os.remove(filepath)
        
        # Analyze transcript
        job_queue.update_job(job_id, progress=70, 
                            message='Analyzing seller motivation...')
        
        analysis = analyzer.analyze_transcript(transcript)
        
        # Get usage stats
        usage_stats = usage_tracker.get_usage_stats(user_id)
        
        # Job complete
        job_queue.update_job(
            job_id, 
            status='complete', 
            progress=100,
            message='Analysis complete!',
            result={
                'success': True,
                'transcript': transcript,
                'analysis': analysis,
                'audio_duration_minutes': round(actual_duration_minutes, 2),
                'usage_stats': usage_stats,
                'timestamp': datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        # Clean up file on error
        if os.path.exists(filepath):
            os.remove(filepath)
        
        # Update job with error
        job_queue.update_job(
            job_id,
            status='error',
            progress=0,
            message='Error processing audio',
            error=str(e)
        )
        
        print(f"Error in async worker for job {job_id}: {str(e)}")


def start_async_job(filepath, user_id, analyzer, usage_tracker, app_config):
    """
    Start a new async processing job
    
    Returns:
        job_id: Unique job identifier
    """
    # Create job
    job_id = job_queue.create_job(user_id)
    
    # Start background thread
    thread = threading.Thread(
        target=process_audio_async,
        args=(job_id, filepath, user_id, analyzer, usage_tracker, app_config),
        daemon=True
    )
    thread.start()
    
    return job_id
