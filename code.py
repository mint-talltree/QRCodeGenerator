from flask import Flask, request, send_file
import segno
import os
import shutil
from werkzeug.utils import secure_filename
from io import BytesIO
import tempfile
import requests

app = Flask(__name__)
UPLOAD_FOLDER = '/tmp/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# HTML template remains the same
HTML_TEMPLATE = '''
<!doctype html>
<html>
<head>
    <title>QR Code Generator</title>
    <style>
        body { 
            font-family: Arial; 
            max-width: 600px; 
            margin: 20px auto; 
            padding: 20px; 
            background: #f5f5f5;
        }
        .container {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        input {
            width: 100%;
            padding: 8px;
            margin-bottom: 5px;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-sizing: border-box;
        }
        input[type="file"] {
            padding: 5px;
        }
        button {
            background: #4CAF50;
            color: white;
            padding: 10px 15px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            width: 100%;
        }
        button:hover {
            background: #45a049;
        }
        .help-text {
            font-size: 0.8em;
            color: #666;
            margin-top: 2px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>QR Code Generator</h1>
        <form action="/generate" method="post" enctype="multipart/form-data">
            <div class="form-group">
                <label for="data">Enter Text or URL:</label>
                <input type="text" id="data" name="data" required>
            </div>
            
            <div class="form-group">
                <label for="file">Upload Background Image:</label>
                <input type="file" id="file" name="file" accept=".png,.jpg,.jpeg,.gif">
                <div class="help-text">Supported formats: PNG, JPG, GIF (max 5MB)</div>
            </div>
            
            <div class="form-group">
                <label for="filename">QR Code Filename:</label>
                <input type="text" id="filename" name="filename" placeholder="my_qr_code">
                <div class="help-text">Enter filename without extension</div>
            </div>
            
            <button type="submit">Generate QR Code</button>
        </form>
    </div>
</body>
</html>
'''

@app.route('/')
def index():
    return HTML_TEMPLATE

@app.route('/generate', methods=['POST'])
def generate_qr():
    data = request.form.get('data')
    file = request.files.get('file')
    filename = request.form.get('filename') or 'qr_code'
    
    if not data:
        return "No data provided", 400

    filename = secure_filename(filename)
    file_extension = 'png'
    
    qr = segno.make(data)
    temp_file_path = None

    if file:
        uploaded_filename = secure_filename(file.filename)
        allowed_extensions = {'.png', '.jpg', '.jpeg', '.gif'}
        file_ext = os.path.splitext(uploaded_filename)[1].lower()
        if file_ext not in allowed_extensions:
            return "Invalid file format. Please upload a PNG, JPG, or GIF image.", 400
        
        # Create a temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, dir=app.config['UPLOAD_FOLDER'], suffix=file_ext)
        file.save(temp_file.name)
        temp_file_path = temp_file.name
        print(f"Using temporary uploaded image: {temp_file_path}")
        file_extension = file_ext[1:].lower()  # Remove dot from extension and convert to lowercase
    
    img_io = BytesIO()
    
    if temp_file_path:
        try:
            output_qr_path = tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}").name
            qr.to_artistic(background=temp_file_path, target=output_qr_path, scale=10, kind='jpeg' if file_extension == 'jpg' else file_extension)
            
            with open(output_qr_path, "rb") as qr_file:
                img_io.write(qr_file.read())
            
            img_io.seek(0)
        except Exception as e:
            return f"Error generating QR code with background: {e}", 400
        finally:
            os.unlink(temp_file_path)  # Delete the uploaded temp file
            os.unlink(output_qr_path)  # Delete the QR code temp file
    else:
        qr.save(img_io, kind='png', scale=10)
        img_io.seek(0)
    
    return send_file(img_io, mimetype=f'image/{file_extension}', as_attachment=True, download_name=f"{filename}.{file_extension}")

if __name__ == '__main__':
    app.run(debug=True)
