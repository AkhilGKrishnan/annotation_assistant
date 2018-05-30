import os
import subprocess
import platform
import shutil
import codecs
import json
import webbrowser
import time
from random import sample
import eel
import jinja2
from github import Github
from github.GithubException import GithubException

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

#---/ Common functions /-------------------------------------------------------
#
class common_functions:

  def load_json(self, path):
    with codecs.open(path, 'r', 'utf-8') as f:
      json_data = json.load(f)
    return json_data
  
  def dump(self, data, filename):
    with codecs.open(filename, 'w', 'utf-8') as dump:
      dump.write(data)

  def get_html(self, url="", path="", repeated=False):
    html = None
    if url:
      try:
        with urlopen(url) as response:
          html = lxml_html.parse(response).getroot()
      except (TimeoutError, URLError) as e:
        if repeated==False:
          print('TimeoutError: %s\nTrying again...' %(url))
          return self.get_html(url=url, repeated=True)
        else:
          print('TimeoutError: %s\nFailed' %(url))
          self.errors.append('TimeoutError: %s' %(url))
          return None
    elif path:
      html = lxml_html.parse(path).getroot()
    return html

#---/ Subprocesses /-----------------------------------------------------------
#
class subprocesses(common_functions):

  def __init__(self):
    self.subprocesses_list = []
    self.pending_lst = []
    self.max = 4
    self.output = ''

  def hide_console(self):
    startupinfo = None
    if os.name == 'nt':
      startupinfo = subprocess.STARTUPINFO()
      startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    return startupinfo
    
  def run(self, cmd, cwd=''):
    if not cwd:
      cwd = os.getcwd()
    self.output+='%s>%s\n' %(cwd, ' '.join(cmd))
    p = subprocess.Popen(cmd,
                         cwd=r'%s' %(cwd),
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT,
                         startupinfo=self.hide_console())
    trace = self.trace_console(p)
    print(trace)
    self.output+=trace+'\n'
    self.dump(self.output, 'console.log')
      
  def trace_console(self, p):
    output = ""
    try:
      for line in iter(p.stdout.readline, b''):
        output += line.rstrip().decode('utf-8')+'\n'
    except ValueError:
      print('subprocess stopped.')
    return output

sp = subprocesses()

#---/ MPAT functions /---------------------------------------------------------
#
class annotation_functions(common_functions):
  """
  Contains Morphology Pre-annotation Tool workflow functions.
  """

  GIT_MPAT = 'git+https://github.com/cdli-gh/morphology-pre-annotation-tool.git'
  GIT_ANNOTATED = 'https://github.com/cdli-gh/mtaac_gold_corpus.git'
  ANNOTATED_ROOT = os.path.join(BASE_DIR, "data")
  ANNOTATED_REPO_NAME = 'mtaac_gold_corpus'
  ANNOTATED_PATH = os.path.join(ANNOTATED_ROOT, ANNOTATED_REPO_NAME)
  TO_ANNOTATE = os.path.join(ANNOTATED_PATH, 'morph', 'to_annotate')
  TO_DICT = os.path.join(ANNOTATED_PATH, 'morph', 'to_dict')
  PROCESSED = os.path.join(ANNOTATED_PATH, 'morph', 'processed')
  progress_json_path = os.path.join(ANNOTATED_PATH, 'morph', 'progress.json')
  branch = 'workflow'
  
  def __init__(self, username, password):
    self.user = username
    self.password = password
    self.actualize()

  def actualize(self):
    '''
    Actualize MPAT and annotated data.
    '''
    self.install_or_upgrade_mpat()
    if not os.path.exists(self.ANNOTATED_ROOT):
      os.makedirs(self.ANNOTATED_ROOT)
    if not os.path.exists(os.path.join(self.ANNOTATED_ROOT,
                                       self.ANNOTATED_REPO_NAME)):
      self.clone_annotated()
    else:
      self.update_annotated()
    self.update_mpat_dict()
    self.load_progress_data()

  def install_or_upgrade_mpat(self):
    '''
    Install MPAT if missing or upgrade it.
    '''
    sp.run(['pip', 'install', self.GIT_MPAT, '--upgrade'])

  def update_mpat_dict(self):
    '''
    Wipe and update MPAT dict.
    '''
    sp.run(['mpat', '-d'])
    sp.run(['mpat', '-n', '-i', self.TO_DICT])    

  def clone_annotated(self):
    '''
    Clone MTAAC annotated repo.
    '''
    sp.run(['git', 'clone', '-b', self.branch, self.GIT_ANNOTATED],
           cwd=self.ANNOTATED_ROOT)

  def update_annotated(self):
    '''
    Update MTAAC annotated repo.
    '''
    sp.run(['git', 'pull', 'origin', self.branch], cwd=self.ANNOTATED_PATH)

  def load_progress_data(self):
    '''
    Load `self.progress_dict` from JSON, when exists,
    or create it as blank dict. Dict. format:
    {'username': {annotating: P00003, done: [P00001, P00002]}
    '''
    if hasattr(self, 'progress_dict'):
      if os.path.exists(self.progress_json_path):
        pd = self.load_json(self.progress_json_path)
        if pd!=self.progress_dict:
          for k in pd.keys():
            if k!=self.user:
              self.progress_dict[k] = pd[k]
    elif os.path.exists(self.progress_json_path):
      self.progress_dict = self.load_json(self.progress_json_path)
    else:
      self.progress_dict = {}
    self.progress_lst = []
    for k in self.progress_dict.keys():
      if self.progress_dict[k]['annotating']!='':
        self.progress_lst.append(self.progress_dict[k]['annotating'])
      self.progress_lst+=self.progress_dict[k]['done']

  def progress_data_annotating_update(self, ID):
    '''
    Add new ID to `self.progress_dict` and `self.progress_lst`.
    Then dump `self.progress_lst` to JSON.
    '''
    self.progress_lst.append(ID)
    if self.user not in self.progress_dict.keys():
     self.progress_dict[self.user] = {'annotating': '', 'done': []}
    self.progress_dict[self.user]['annotating'] = ID
    self.update_progress_data()

  def progress_data_ready_update(self):
    '''
    Move annotated ID to "done" list in `self.progress_dict`.
    Then dump `self.progress_lst` to JSON.
    '''
    ID = self.progress_dict[self.user]['annotating']
    self.progress_dict[self.user]['done'].append(ID)
    self.progress_dict[self.user]['annotating'] = ''
    self.update_progress_data()

  def update_progress_data(self):
    '''
    Dump `self.progress_lst` to JSON.
    '''
    self.dump(json.dumps(self.progress_dict), self.progress_json_path)

  def select_new_text(self):
    '''
    Select new text workflow:
    1. Create `self.PROCESSED` dir if not exists
    2. Select random text to annotate
    3. Copy .conll file to `self.PROCESSED`
    4. Preannotate .conll file
    5. Update and dump `self.progress_lst`.
    Return True when successful and False when there is already a choosen text.
    '''
    self.actualize()
    if not os.path.exists(self.PROCESSED):
      os.makedirs(self.PROCESSED)
    if self.user in self.progress_dict.keys():
      if self.progress_dict[self.user]['annotating']!='':
        return False
    ID = self.select_random_to_annotate()
    dest = os.path.join(self.PROCESSED, '%s.conll' %ID)
    shutil.copyfile(os.path.join(self.TO_ANNOTATE, '%s.conll' %ID),
                    dest)
    self.preannotate_and_replace(dest)
    self.progress_data_annotating_update(ID)
    git_message = 'Select %s.conll for annotation by %s' %(ID, self.user)
    self.update_github(git_message)
    return True

  def select_random_to_annotate(self):
    '''
    Select random .conll file from `self.TO_ANNOTATE`,
    which is not in `self.progress_dict`.
    '''
    to_annotate_lst = [f.split('.')[0] for f in os.listdir(self.TO_ANNOTATE)
                       if f.split('.')[1]=='conll' and f.split('.')[0] not in
                       self.progress_lst]
    return sample(to_annotate_lst, len(to_annotate_lst))[0]

  def preannotate_and_replace(self, path):
    '''
    Preannotate .conll file in given path and replace the original
    with it.
    '''
    root_path = os.path.abspath(os.path.join(path, os.pardir))
    filename = os.path.basename(path)
    sp.run(['mpat', '-i', path])
    os.remove(path)
    shutil.move(os.path.join(root_path, 'output', filename),
                path)
    shutil.rmtree(os.path.join(root_path, 'output'))

  def convert_and_push(self):
    '''
    Push text workflow:
    1. Run mpat with -f switch to format the conll files for
      next Conll-U convertor
    2. Update `self.progress_dict`.
    3. Move .conll file from `self.PROCESSED` to `self.TO_DICT`
    4. Push changes to repo.
    '''
    self.actualize()
    ID = self.progress_dict[self.user]['annotating']
    self.convert_to_conll_U(ID)
    target = os.path.join(self.PROCESSED, '%s.conll' %ID)
    dest = os.path.join(self.TO_DICT, '%s.conll' %ID)
    shutil.move(target, dest)
    self.progress_data_ready_update()
    git_message = 'Add annotated %s.conll by %s' %(ID, self.user)
    self.update_github(git_message)

  def convert_to_conll_U(self, ID):
    '''
    Run mpat with -f switch to format the conll files for
    next Conll-U convertor. Then replace the original
    with it.
    '''
    file_path = os.path.join(self.PROCESSED, '%s.conll' %ID)
    output_path = os.path.join(self.PROCESSED, 'output', '%s.conll' %ID)
    sp.run(['mpat', '-f', '-i', file_path])
    shutil.move(output_path, file_path)
    shutil.rmtree(os.path.join(self.PROCESSED, 'output'))

  def update_github(self, message):
    '''
    Push repo to GitHub.
    '''
    repo_data = 'https://%s:%s@%s' %(self.user,
                                     self.password,
                                     self.GIT_ANNOTATED.split('//')[1])
    sp.run(['git', 'checkout', '-b', self.branch], cwd=self.ANNOTATED_PATH)
    sp.run(['git', 'add', '.'], cwd=self.ANNOTATED_PATH)
    sp.run(['git', 'commit', '-a','-m', message], cwd=self.ANNOTATED_PATH)
    sp.run(['git', 'push', repo_data, self.branch],
           cwd=self.ANNOTATED_PATH)
    
#---/ Dashboard scripts /------------------------------------------------------
#
class Dashboard(common_functions):

  def __init__(self):
    self.primary = True

  def login_view(self):
    self.templates_manager("login", {})

  def new_text_view(self):
    self.templates_manager("new_text",
                           {"username": self.login_data['username']})

  def annotation_view(self):
    ID = self.af.progress_dict[self.af.user]['annotating']
    self.templates_manager("annotate",
                           {"username": self.login_data['username'],
                            "textID": ID})
    
  def annotation_status_check(self):
    if self.af.user not in self.af.progress_dict.keys():
      return 'add new'
    elif self.af.progress_dict[self.af.user]['annotating']=='':
      return 'add new'
    return 'annotate'

  def github_login_check(self, username, password):
    try:
      g = Github(username, password)
      repos_lst = [x.full_name for x in g.get_user().get_repos()]
      if 'cdli-gh/mtaac_gold_corpus' in repos_lst:
        return True
      return None
    except GithubException as e:
      return False

  def github_login(self, json_data):
    login_data = json.loads(json_data)
    login_check = self.github_login_check(login_data["username"],
                                          login_data["password"])
    if login_check in [None, False]:
      eel.login_error()
    else:
      self.login_data = login_data
      self.plug_annotation_backend()
      status = self.annotation_status_check()
      if status=='add new':
        self.new_text_view()
      elif status=='annotate':
        self.annotation_view()
  
  def plug_annotation_backend(self):
    self.af = annotation_functions(self.login_data["username"],
                                   self.login_data["password"])

  def select_new_text(self):
    self.af.select_new_text()
    time.sleep(10)
    self.annotation_view()

  def convert_and_push(self):
    self.af.convert_and_push()
    self.new_text_view()

  def templates_manager(self, template, args_dict):
    '''
    Shortcut to render template and reload the page.
    '''
    t = self.render_template("templates/%s.html" %(template), args_dict)
    with codecs.open('static/index.html', 'w', 'utf-8') as f:
      f.write(t)
    if self.primary==True:
      self.primary = False
      eel.start('index.html')
    else:
      print('reloading view')
      eel.reload()

  def render_template(self, path, context):
    path, filename = os.path.split(path)
    return jinja2.Environment(
        loader=jinja2.FileSystemLoader(path or './')
    ).get_template(filename).render(context)

  def open_dir(self):
    '''
    Open directory in system viewer.
    '''
    ID = self.af.progress_dict[self.af.user]['annotating']
    path = os.path.join(self.af.PROCESSED, '%s.conll' %ID)
    if platform.system()=="Windows":
      subprocess.Popen(["explorer", "/select,", path])
    elif platform.system()=="Darwin":
      subprocess.Popen(["open", path])
    else:
      subprocess.Popen(["xdg-open", path])

  def open_page(self):
    ID = self.af.progress_dict[self.af.user]['annotating']
    url = "https://cdli.ucla.edu/search/archival_view.php?ObjectID=%s" %ID
    webbrowser.open(url)

#---/ Eel functions /----------------------------------------------------------
#

eel.init('static')
d = Dashboard()

@eel.expose
def github_login(json_data):
  print('check github login data')
  d.github_login(json_data)    

@eel.expose
def select_new_text():
  print('selecting new text')
  d.select_new_text()

@eel.expose
def convert_and_push():
  print('converting and pushing')
  d.convert_and_push()

@eel.expose
def open_dir():
  print('opening directory')
  d.open_dir()
  
@eel.expose
def open_page():
  print('opening web page')
  d.open_page()

#---/ Main /-------------------------------------------------------------------
#
if __name__ == "__main__":
  d.login_view()



