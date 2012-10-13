from flask import Flask, render_template, request
from flask.views import MethodView

import os
from datetime import datetime
import json
import logging

from mongoengine import Document, DateTimeField, ListField, StringField, connect

sessions_map = [
    'content1', 'content2', 'content3', 'content4',
    'developer1', 'developer2', 'developer3', 'developer4',
    'marketing1', 'marketing2', 'marketing3', 'marketing4',
    'intro1', 'intro2'
]


class TCVoteDocument(Document):
    # the time of the vote (best practice)
    timestamp = DateTimeField()
    # the session(s) selected
    sessions = ListField(StringField())
    # the IP of the user
    ip_address = StringField()


class MainView(MethodView):
    # just return the voting interface
    def get(self):
        return render_template('main.html')


class VoteView(MethodView):
    def post(self):
        # expect a JSON array of strings which are the sessions selected
        sessions = json.loads(request.values['sessions'])
        timestamp = datetime.now()

        # create a new entry
        vote_doc = TCVoteDocument(
            timestamp=timestamp,
            sessions=sessions,
            ip_address=request.remote_addr
        )
        # insert
        vote_doc.save()

        # make jQuery happy
        return json.dumps({"message": "success"})


class ResultsView(MethodView):
    def get(self):
        # for the template
        template_values = {}
        for session in sessions_map:
            # get all of the rows which contain votes for a particular session
            # look ma .. no joins!
            query = TCVoteDocument.objects(sessions=session)
            # store the count to be displayed in the template
            template_values[session] = query.count()

        return render_template('results.html', template_values=template_values)

# one of the few things I don't like about Flask
main_view_func = MainView.as_view('main_view')
vote_view_func = VoteView.as_view('vote_view')
results_view_func = ResultsView.as_view('results_view')

app = Flask(__name__)

# set up the endpoints
app.add_url_rule('/vote', view_func=vote_view_func, methods=['POST', ])
app.add_url_rule('/results', view_func=results_view_func, methods=['GET', ])
app.add_url_rule('/', view_func=main_view_func, methods=['GET', ])

if __name__ == '__main__':
    host = 'localhost'
    port = int(os.getenv('PORT', 5000))

    # we are on heroku
    if not port == 5000:
        host = '0.0.0.0'
        # database connection string left out because it contains a password
    # running locally
    else:
        connect('tcvote')
    app.debug = True
    app.run(host=host, port=port)
