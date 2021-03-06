from pathlib import Path
from flask import Flask, request, make_response, redirect
import os
import numpy as np
import search

app = Flask(__name__, static_url_path="")


extracted_features = np.zeros((10000, 2048), dtype=np.float32)
with open('saved_features_recom.txt') as f:
    for i, line in enumerate(f):
        extracted_features[i, :] = line.split()
print("loaded extracted_features")


id_tag_dict = {}
for f in Path('database/tags').glob('*'):
    tag_name = os.path.splitext(f.name)[0]
    if tag_name.endswith('_r1'):
        tag_name = tag_name[:-3]
    with open(f, 'r') as fp:
        for line in fp:
            try:
                image_id = line.strip()
                id_tag_dict.setdefault(image_id, set())
                id_tag_dict[image_id].add(tag_name)
            except Exception as ex:
                print(f.name, fp.tell(), line)
                print(ex)
print("loaded id_tag_dict")


@app.route('/image/<int:image_id>', methods=['GET'])
def get_image(image_id):
    headers = {
        "Content-Disposition": f"attachment; filename=im{image_id}.jpg",
        "Content-Type": "image/jpeg",
        "Cache-Control": "public, max-age=43200"
    }
    with open(f'database/dataset/im{image_id}.jpg', 'rb') as f:
        body = f.read()
    return make_response((body, headers))


@app.route('/imgUpload', methods=['GET', 'POST'])
def upload_img():
    # check if the post request has the file part
    if 'file' not in request.files:
        return 'No file', 400

    file = request.files['file']
    count = request.values.get('count', 9)

    image_id_list = search.recommend(file.read(), extracted_features, count)
    print(image_id_list)

    return {
        'images': [{
            'id': image_id,
            'tag': list(id_tag_dict.get(image_id, []))
        } for image_id in image_id_list]
    }


@app.route("/")
def index():
    return redirect("/index.html", 301)


@app.route("/favorite")
def favorite():
    return redirect("/favorite.html", 301)


@app.route("/get_tag", methods=["POST"])
def get_tag():
    image_id_list = request.get_json(force=True)
    return {
        'images': [{
            'id': image_id,
            'tag': list(id_tag_dict[image_id])
        } for image_id in image_id_list
            if image_id in id_tag_dict]
    }


if __name__ == '__main__':
    app.run(debug=True, host='localhost')
