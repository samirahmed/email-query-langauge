import nltk, json, time, sys
from termcolor import colored

class abstract_syntax_tree:
  
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
      'tree' : self.tree.pprint() if self.tree else "()",
    }

  def json(self):
    return json.dump(self.properties(), indent=2)

  def normalize(self, debug):
    
    debug.write("\n" + self.query)
    self.normalized = []
    self.wildcards = []

    words = self.query.lower().split()
    for word in words:
      if word in self.terminals:
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
      return False
    else:
      sys.stdout.write( colored('.', 'green'))
      debug.write(str( self.tree) + "\n")

class nlq:
  sender          = None
  recipients      = None
  first_text      = None
  second_text     = None
  conjunction     = None
  has_attachments = None
  attachments     = None
  date            = None
  date_is_parsed  = None
  date_comparator = None
  link            = None
  has_links       = None
  scope           = None
  query           = None

  index = 0

  def __init__(self, ast):
    self.query = ast.query
    self._visit(ast.tree, ast.wildcards)
    index = 0
  
  def __str__(self):
    return str(self.properties())

  def parse_terms(self):
    terms = {}

    if self.sender:
      terms["sender"] = self.sender
    if self.recipients:
      terms["recipients"] = self.recipients
    if self.first_text and self.second_text and self.conjunction:
      terms["query"] = "%s %s %s" % (self.first_text, self.conjunction, self.second_text)
    elif self.first_text:
      terms["query"] = self.first_text
    if self.attachments:
      terms["attachments"] = self.attachments
    if self.link:
      terms["link"] = self.link
    if self.scope and self.date:
      terms["date"] = self.date
    elif self.date_comparator and self.date:
      terms["date"] = self.date_comparator + " " + self.date

    return terms

  def properties(self):
    return {
     'sender': self.sender,
     'recipients': self.recipients,
     'first_text': self.first_text,
     'second_text': self.second_text,
     'conjunction': self.conjunction,
     'attachments': self.attachments,
     'has_attachments': self.has_attachments,
     'link': self.link,
     'has_links': self.has_links,
     'date': self.date,
     'date_comparator': self.date_comparator,
     'scope': self.scope
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
      self.has_attachments = True
      self.index += 1

    elif tree.node == "HASP":  # Has Attachment Specifier
      self.has_attachments = True

    elif tree.node == "NASP": # Not Has Attachment Specifier
      self.has_attachments = False

    elif tree.node == "STSP":  # Single Text Specifier
      self.first_text = wildcards[self.index]
      self.index += 1

    elif tree.node == "CTSP":  # Conjunctive Text Specifier
      self.first_text = wildcards[self.index]
      self.second_text = wildcards[self.index+1]
      self.conjunction = "and" if tree.leaves()[-2] == "and" else "or"
      self.index += 2

    elif tree.node == "TLSP":   # Text Link Specifier
      self.has_links = True
      self.link = wildcards[self.index]
      self.index += 1

    elif tree.node == "HLSP":  # Has Link Specifier
      self.has_links = True

    elif tree.node == "NLSP":  # Not Has Link Specifier
      self.has_links = False
    
    elif tree.node == "DSP":   # DateTime Specifier
      self.date = wildcards[self.index]
      if tree.leaves()[-2] == "after":
          self.date_comparator = "after"
      elif tree.leaves()[-2] == "before":
          self.date_comparator = "before"
      self.index += 1
  
    for subtree in tree:
      self._visit(subtree, wildcards)
  
def parse(email_parser, terminals, query, debug):
  ast = abstract_syntax_tree(email_parser, terminals, query, debug)
  eq = nlq(ast)
  return ast, eq

