import nltk
import json
import time
import re
import sys
from termcolor import colored

class AbstractSyntaxTree:
  
  duration = None
  tree = None
  wildcards = None
  normalized_query = None
  query = None
  terminals = None
  parser = None

  def __init__(self, parser, terminals, query, debug):
    
    start = time.time()
    self.parser = parser
    self.terminals = terminals
    self.query = query
    
    self.normalize(debug)
    self.parse(debug)
    self.duration = time.time() - start

  def __str__(self):
    return str(self.properties())

  def properties(self):
    return {
      'duration': self.duration,
      'query' : self.query,
      'normalized_query' : self.normalized,
      'wildcards' : self.wildcards,
      'tree' : self.tree.pprint(),
    }

  def json(self):
    return json.dump(self.properties(), indent=2)

  def normalize(self, debug):
    
    debug.write("\n" + self.query)
    self.normalized = []
    self.wildcards = []

    words = self.query.lower().split()
    for word in words:
      if word in terminals:
        self.normalized.append(word)
      else:
        if len(self.normalized) == 0 or self.normalized[-1] != 'term':
          self.normalized.append('term')
          self.wildcards.append(word)
        else:
          self.wildcards[-1] += " " + word
    
    debug.write("NORMALIZED: " + " ".join(self.normalized) + "\n")
    debug.write("WILDCARDS: %s \n" % self.wildcards)

  def parse(self, debug):
   
    self.tree = self.parser.parse(self.normalized)
    
    if not self.tree:
      print colored("ERROR PARSING %s " % self.query, 'red'),
      debug.write("PARSE ERROR \n")
      return false
    else:
      sys.stdout.write( colored('.', 'green'))
      debug.write(str( self.tree) + "\n")

class EmailQuery:
  
  sender          = None
  recipients      = None
  first_text      = None
  second_text     = None
  conjunction     = None
  attachments     = None
  date            = None
  date_comparator = None
  link            = None

  index = 0

  def __init__(self, ast):
    self._visit(ast.tree, ast.wildcards)
    index = 0
  
  def __str__(self):
    return str(self.properties())

  def properties(self):
    return {
     'sender': self.sender,
     'recipients': self.recipients,
     'first_text': self.first_text,
     'second_text': self.second_text,
     'conjunction': self.conjunction,
     'attachments': self.attachments,
     'link': self.link,
     'date': self.date,
     'date_comparator' : self.date_comparator
    }

  def json(self):
    return json.dumps(self.properties(), indent = 2)

  def _visit(self, tree, wildcards):
    
    if not tree or not (type(tree) == nltk.tree.Tree):
      return

    if tree.node == "TCSP":    # To Contact Specifier
      self.recipients = wildcards[self.index]
      self.index += 1

    elif tree.node == "FCSP":  # From Contact Specifier
      self.sender = wildcards[self.index]
      self.index += 1

    elif tree.node == "FTCSP": # From To Contact Specifier
      self.sender = wildcards[self.index]
      self.recipients = wildcards[self.index+1]
      self.index += 2

    elif tree.node == "TFCSP": # To From Contact Specifier 
      self.recipients = wildcards[self.index]
      self.sender = wildcards[self.index+1]
      self.index += 2

    elif tree.node == "FASP":  # Filename Attachment Specifier
      self.attachments = wildcards[self.index]
      self.index += 1

    elif tree.node == "STSP":  # Single Text Specifier
      self.first_text = wildcards[self.index]
      self.index += 1

    elif tree.node == "CTSP":  # Conjunctive Text Specifier
      self.first_text = wildcards[self.index]
      self.second_text = wildcards[self.index+1]
      self.conjunction = "and" if tree.leaves()[-2] == "and" else "or"
      self.index += 2

    elif tree.node == "LSP":   # Link Specifier
      self.link = wildcards[self.index]
      self.index += 1
    
    elif tree.node == "DSP":   # DateTime Specifier
      self.date = wildcards[self.index]
      self.date_comparator = "after" if tree.leaves()[-2] == "after" else "before"
      self.index += 1
  
    for subtree in tree:
      self._visit(subtree, wildcards)

lines = open("email.cfg").readlines()
grammar = '\n'.join(filter(lambda line: not line.startswith("%"),lines))
cfg = nltk.parse_cfg(grammar)
email_parser = nltk.LeftCornerChartParser(cfg)

# get a set of all terminals in the grammar
terminals = set(re.findall(r'[\"\'](.+?)[\"\']',grammar))
count = 0

with  open("test.result","w") as debug: 
  debug.write("Terminals %s" % terminals)
  for line in open('./queries.txt').readlines():
    if line and not line.startswith("#") and len(line.split()) > 0:
      ast = AbstractSyntaxTree(email_parser, terminals, line, debug)
      result = EmailQuery(ast)
      debug.write((result).json())
      debug.write("duration %f \n" % ast.duration)
      count += 1
      if count % 50 == 0:
        sys.stdout.write("\n")
      sys.stdout.flush()

print "\n%d lines parsed" % count
