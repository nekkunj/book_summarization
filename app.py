from flask import Flask, render_template, request, redirect, url_for
from featureEng import *
import os

app = Flask(__name__)

# Get the absolute path of the directory where the script is located
base_dir = os.path.abspath(os.path.dirname(__file__))

# Set the upload folder to be a subdirectory named 'uploads'
app.config['UPLOAD_FOLDER'] = os.path.join(base_dir, 'uploads')

@app.route('/')
def index():
    return render_template('upload.html')

@app.route('/', methods=['POST'])
def upload():
    # Check if the post request has the file part
    if 'file' not in request.files:
        return redirect(request.url)
    transformer_model = request.form['transformer']
    file = request.files['file']
    print(transformer_model)
    # If the user does not select a file, the browser submits an empty part without a filename
    if file.filename == '':
        return redirect(request.url)

    if file:
        # Save the file to the upload folder
        filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filename)
        # print(filename)
        summaries,average_rouge_1_r,average_rouge_2_r,average_rouge_l_r,average_rouge_1_p,average_rouge_2_p,average_rouge_l_p,average_rouge_1_f,average_rouge_2_f,average_rouge_l_f=parse_pdf(filename,transformer_model)
        return render_template('display.html', summaries=summaries,
                                               average_rouge_1_r=average_rouge_1_r,
                                               average_rouge_2_r=average_rouge_2_r,
                                               average_rouge_l_r=average_rouge_l_r,
                                               average_rouge_1_p=average_rouge_1_p,
                                               average_rouge_2_p=average_rouge_2_p,
                                               average_rouge_l_p=average_rouge_l_p,
                                               average_rouge_1_f=average_rouge_1_f,
                                               average_rouge_2_f=average_rouge_2_f,
                                               average_rouge_l_f=average_rouge_l_f,
                            )


    
if __name__ == '__main__':
    app.run(debug=True)
