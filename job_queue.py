"""
Simple in-memory job queue for async audio processing
Stores job status and results temporarily
"""
import uuid
import threading
from datetime import datetime, timedelta
from typing import Dict, Optional, Any

class JobQueue:
    def __init__(self):
        self.jobs: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()
        
    def create_job(self, user_id: str = "anonymous") -> str:
        """Create a new job and return job ID"""
        job_id = str(uuid.uuid4())
        
        with self.lock:
            self.jobs[job_id] = {
                'job_id': job_id,
                'user_id': user_id,
                'status': 'queued',  # queued, processing, complete, error
                'progress': 0,
                'message': 'Job queued for processing',
                'created_at': datetime.now(),
                'updated_at': datetime.now(),
                'result': None,
                'error': None
            }
        
        return job_id
    
    def update_job(self, job_id: str, status: str = None, progress: int = None, 
                   message: str = None, result: Any = None, error: str = None):
        """Update job status and details"""
        with self.lock:
            if job_id not in self.jobs:
                return False
            
            job = self.jobs[job_id]
            
            if status:
                job['status'] = status
            if progress is not None:
                job['progress'] = progress
            if message:
                job['message'] = message
            if result is not None:
                job['result'] = result
            if error:
                job['error'] = error
            
            job['updated_at'] = datetime.now()
            
        return True
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job details by ID"""
        with self.lock:
            return self.jobs.get(job_id)
    
    def delete_job(self, job_id: str):
        """Delete a job from queue"""
        with self.lock:
            if job_id in self.jobs:
                del self.jobs[job_id]
    
    def cleanup_old_jobs(self, hours: int = 24):
        """Remove jobs older than specified hours"""
        cutoff = datetime.now() - timedelta(hours=hours)
        
        with self.lock:
            jobs_to_delete = [
                job_id for job_id, job in self.jobs.items()
                if job['created_at'] < cutoff
            ]
            
            for job_id in jobs_to_delete:
                del self.jobs[job_id]
        
        return len(jobs_to_delete)

# Global job queue instance
job_queue = JobQueue()
