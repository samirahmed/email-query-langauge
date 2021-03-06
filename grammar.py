import nltk, sys, re, os, json
import abstract_syntax_tree
import nlq

def generate(aggregate, remaining, left, so_far = []):
  if left < 0:
    aggregate.append("S -> " + " ".join(so_far))
    return
  
  for term in remaining:
    
    updated = list(so_far)
    updated.append(term)

    diff = set(remaining)
    diff = diff.difference(set([term]))
    
    generate(aggregate, diff, left-1, updated)

def bootstrap_grammar(lines):
  atomic_specifier_phrases = set(lines[0][1:].split())
  grammar_lines = filter(lambda line: not line.startswith("%"),lines)
  
  additional_lines = []

  for size in range(len(atomic_specifier_phrases)):
    generate(additional_lines, atomic_specifier_phrases, size)

  additional_lines.extend(grammar_lines)
  return additional_lines

lines = open("email.cfg").readlines()
raw_cfg = '\n'.join(bootstrap_grammar(lines))

with open("processed_grammar.result", "w") as processed_grammar:
  processed_grammar.write(raw_cfg)

cfg = nltk.parse_cfg(raw_cfg)
email_parser = nltk.LeftCornerChartParser(cfg)

# get a set of all terminals in the grammar
terminals = set(re.findall(r'[\"\'](.+?)[\"\']',raw_cfg))
count = 0

with open("test.result","w") as debug: 
  debug.write("Terminals %s" % terminals)
  for line in open('./queries.txt').readlines():
    if line and not line.startswith("#") and len(line.split()) > 0:
      ast, eq = nlq.parse(email_parser, terminals, line , debug)
      result = {"ast" : ast.properties() , "eq": eq.properties() }
      debug.write(json.dumps(result, indent = 2))
      debug.write("duration %f \n" % ast.duration)
      count += 1
      if count % 50 == 0:
        sys.stdout.write("\n")
      sys.stdout.flush()

def process(query, debug):
  global email_parser
  global terminals
  return nlq.parse(email_parser, terminals, query, debug)
  
print "\n%d lines parsed" % count
