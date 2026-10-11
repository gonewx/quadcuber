from html.parser import HTMLParser
from pathlib import Path
class Check(HTMLParser):
 def __init__(self):super().__init__();self.stack=[];self.ids=set();self.fullscreen=set()
 def handle_starttag(self,tag,attrs):
  a=dict(attrs);ident=a.get('id')
  if ident:assert ident not in self.ids,ident;self.ids.add(ident)
  if ident and 'viewport-shell' in self.stack:self.fullscreen.add(ident)
  if tag not in ['meta','link','img','input','br','hr']:self.stack.append(ident or tag)
 def handle_endtag(self,tag):
  if self.stack:self.stack.pop()
for page in ['index.html','integrated-assembly.html']:
 c=Check();c.feed(Path('dist',page).read_text())
 if 'assembly' in page:
  for n in ['step-next','step-progress-bottom','view-step-title','expanded-check','expanded-instructions']:assert n in c.fullscreen,n
 print(page,'unique IDs:',len(c.ids),'fullscreen children verified')
