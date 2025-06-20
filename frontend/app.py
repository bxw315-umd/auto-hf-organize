from flask import Flask, render_template, request, Response, stream_with_context
import json
import os
import threading
import queue
import shutil
import uuid
from datetime import datetime
import sys
from pathlib import Path

# Add parent directory to path to import run_agent
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from run_agent import main as run_agent, copy_dir

app = Flask(__name__)

# In-memory log storage and queue for SSE
log_entries = []
log_queue = queue.Queue()

ROOT = os.getcwd()
USER_FILES_BASE = os.path.join('outputs', 'uploaded_files')
MY_FILES_DIR = os.path.join(ROOT, "my_files")
os.makedirs(USER_FILES_BASE, exist_ok=True)

def emit_log(log):
    log_entries.append(log)
    log_queue.put(log)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/log', methods=['POST'])
def receive_log():
    log = request.get_json(force=True)
    emit_log(log)
    return {'status': 'ok'}, 200

@app.route('/upload', methods=['POST'])
def upload():
    # Store uploaded files in outputs/user_files/<unique_subdir>
    unique_id = datetime.now().strftime('%Y%m%d_%H%M%S_') + str(uuid.uuid4())[:8]
    user_dir = os.path.join(USER_FILES_BASE, unique_id)
    for file in request.files.getlist('files'):
        rel_path = file.filename
        abs_path = os.path.join(user_dir, rel_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        file.save(abs_path)
    
    # Get experiment context from form data with validation
    experiment_context = request.form.get('experimentContext', '')
    
    # Validate context is a string
    if not isinstance(experiment_context, str):
        experiment_context = str(experiment_context) if experiment_context is not None else ''
    
    # Start processing in a background thread
    threading.Thread(target=process_dataset, args=(user_dir, experiment_context), daemon=True).start()
    return {'status': 'uploaded', 'user_dir': user_dir}, 200

def process_dataset(dataset_dir, experiment_context):
    # Copy generic files from my_files into the unique user directory
    copy_dir(Path(MY_FILES_DIR), Path(dataset_dir))

    # Run the agent with context
    result = run_agent(logger_type="http", context=experiment_context)
    
    # Emit the final response
    emit_log({
        "type": "final_response",
        "response": result
    })

@app.route('/stream')
def stream():
    def event_stream():
        # Send all previous logs first
        for log in log_entries:
            yield f'data: {json.dumps(log, ensure_ascii=False)}\n\n'
        # Then stream new logs as they arrive
        while True:
            log = log_queue.get()
            yield f'data: {json.dumps(log, ensure_ascii=False)}\n\n'
    return Response(stream_with_context(event_stream()), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=8000, threaded=True)