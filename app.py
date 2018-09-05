from flask import Flask, jsonify

app = Flask(__name__)

from app import song_dataset

df = song_dataset.df
@app.route('/songs')
def songs():
    title_counts = df[ df['show_date'] > '2017-01-01' ]['title'].value_counts()
    title_counts = title_counts[title_counts > 5]
    title_data = {}
    for title in title_counts.to_dict().keys():
        title_data[title] = song_dataset.song_data(title)

    return jsonify( { 'titles': title_counts.to_dict(), 'title_data': title_data  } )

if __name__ == '__main__':
    app.run()