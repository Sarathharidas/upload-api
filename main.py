from flask import Flask, request, send_file
import os
from werkzeug.utils import secure_filename
import subprocess
import requests
from datetime import timedelta
from flask import jsonify
app = Flask(__name__)

@app.route("/upload", methods=["POST"])
def upload():

    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    if 'language' not in request.form:
        return jsonify({'error': 'No language provided'}), 400
    language = request.form['language']
    filename = secure_filename(file.filename)
    video_file_only_name = filename[0:filename.find('.')]
    video_folder_path = os.path.join(os.getcwd(), video_file_only_name)
    if not os.path.exists(video_folder_path):
      os.makedirs(video_folder_path)
    video_file_path_full = os.path.join(video_folder_path, filename)
    if not os.path.isfile(os.path.join(video_folder_path, filename)):
        file.save(os.path.join(video_folder_path, filename))
        # redirect the user to the uploaded file's URL
    wav_file_path = os.path.join(video_folder_path, video_file_only_name+'.wav')
    command = "ffmpeg -i {0} -ab 160k -ac 2 -ar 44100 -vn {1}".format(video_file_path_full, wav_file_path)
    if not os.path.isfile(wav_file_path):
        subprocess.call(command, shell=True)
    srtFilename = whisper_api(wav_file_path, video_folder_path, language)
    os.remove(video_file_path_full)
    os.remove(wav_file_path)
    #return {'file_path':video_file_path_full,' wav_file_path':wav_file_path }
    return send_file(srtFilename, as_attachment=True)

def whisper_api(audio_wav_path, video_folder_path, language):
  url = "https://transcribe.whisperapi.com"
  headers = {
'Authorization': 'Bearer GLA2TKCWBN41E3H2Q15KKTXEXCQEF7SK'  
}
  file = {'file': open(audio_wav_path, 'rb')}
  data = {

  "diarization": "false",
  #Note: setting this to be true will slow down results.
  #Fewer file types will be accepted when diarization=true
  #"numSpeakers": "2",
  #if using diarization, you can inform the model how many speakers you have
  #if no value set, the model figures out numSpeakers automatically!
   #can't have both a url and file sent!, 
   "task":"translate",
   "language":language
}
  response = requests.post(url, headers=headers, files=file, data=data)
  #print(response.text)

  response_json = response.json()
  segments = response_json['segments']
  segmentId = 0
  for segment in segments:
    startTime = str(0)+str(timedelta(seconds=int(segment['start'])))+',000'
    endTime = str(0)+str(timedelta(seconds=int(segment['end'])))+',000'
    text = segment['text']
    segmentId = segmentId +1
    segment_text = f"{segmentId}\n{startTime} --> {endTime}\n{text[1:] if text[0] is ' ' else text}\n\n"
    srtFilename = os.path.join(video_folder_path, 'english_subtitles.srt')
    
    with open(srtFilename, 'a', encoding='utf-8') as srtFile:
      srtFile.write(segment_text) 
  return srtFilename



if __name__ == "__main__":
    app.run(debug=True)


