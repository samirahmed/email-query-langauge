import json
import requests
import yaml

config = None

def GetConfig():
    global config
    if config is None:
        config = yaml.load(open("config.yaml"))
    return config

class ElasticSearchQuery:
    query = {}
    config = None

    # create your query. Pass null for any unused values
    def __init__(self, nlq): 
        recipients = nlq.recipients
        sender = nlq.sender
        start_time = None
        end_time = None
        body_terms = []

        if nlq.date_comparator == "before":
          end_time = nlq.date.strftime('%Y-%m-%dT%H:%M:%S')
        elif nlq.date_comparator == "after":
          start_time = nlq.date.strftime('%Y-%m-%dT%H:%M:%S')

        if nlq.first_text:
          body_terms.append(nlq.first_text)
        if nlq.second_text:
          body_terms.append(nlq.second_text)
        
        boolDict={}
        shouldList = []
        mustList = []

        if recipients is not None:
            for i in range (0, len(recipients)):
                shouldList.append(self.makeTerm("recipients", recipients[i]))
        if sender is not None:
            shouldList.append(self.makeTerm("sender", sender))
        if body_terms is not None:
            for i in range (0, len(body_terms)):
                shouldList.append(self.makeTerm("body",body_terms[i]))
        if start_time is not None or end_time is not None:
            mustList.append(self.makeRange(start_time, end_time))

        boolDict["should"] = shouldList
        boolDict["must"] = mustList
        self.query["bool"] = boolDict

    def __str__(self):
        return str(self.properties())

    def properties(self):
        return {"query": self.query}

    # use this to generate the json payload for your query
    def json(self):
        return json.dumps(self.properties(), indent=2)

    def makeTerm(self, name, value):
        term = {}
        term[name]={}
        term[name]["value"] = value.lower()
        return {"term": term}

    def makeRange(self, start, end):
        range = {}
        range["dateSent"] = {}
        if start is not None:
            range["dateSent"]["from"] = start
        if end is not None:
            range["dateSent"]["to"] = end
        return {"range": range}

    def sendQuery(self):
        r = requests.post(GetConfig()["emailDbUrl"], data = self.json())
        return r.content
