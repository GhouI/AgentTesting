import os
from flask import Flask, request, jsonify, send_file, make_response
from services import run_project_builder
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
GENERATED_CONTENT_DIR = os.path.join(os.path.dirname(__file__), 'generated_content')

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.route('/api/build_project', methods=['POST', 'OPTIONS'])
def api_build_project():
    if request.method == "OPTIONS":
        return _build_cors_preflight_response()
    elif request.method == "POST":
        data = request.json
        project_description = data.get('project_description')
        project_name = data.get('project_name')
        
        if not project_description or not project_name:
            return jsonify({"error": "Missing project description or name"}), 400
        
        messages, zip_filename = run_project_builder(project_description, project_name)
        
        if zip_filename and not zip_filename.startswith("Error"):
            download_url = f"{request.url_root}download/{zip_filename}"
            messages.append({
                'role': 'assistant',
                'content': f"Project has been zipped successfully. You can download it using the provided link.",
                'downloadUrl': download_url
            })
            return jsonify({
                "messages": messages
            })
        else:
            error_message = zip_filename if zip_filename else "Zip file not created"
            return jsonify({
                "messages": messages,
                "error": error_message
            })
    else:
        raise RuntimeError("Weird - don't know how to handle method {}".format(request.method))

@app.route('/download/<filename>')
def download(filename):
    file_path = os.path.join(GENERATED_CONTENT_DIR, filename)
    app.logger.info(f"Attempting to download file: {file_path}")
    if os.path.exists(file_path):
        app.logger.info(f"File found, sending: {file_path}")
        return send_file(file_path, as_attachment=True)
    else:
        app.logger.error(f"File not found: {file_path}")
        return "File not found", 404

def _build_cors_preflight_response():
    response = make_response()
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add('Access-Control-Allow-Headers', "Content-Type,Authorization")
    response.headers.add('Access-Control-Allow-Methods', "GET,PUT,POST,DELETE,OPTIONS")
    return response

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
