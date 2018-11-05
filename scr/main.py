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
  '''
  '''
  def load_json(self, path):
    '''
    '''
    with codecs.open(path, 'r', 'utf-8') as f:
      json_data = json.load(f)
    return json_data
  
  def dump(self, data, filename):
    '''
    '''
    with codecs.open(filename, 'w', 'utf-8') as dump:
      dump.write(data)

  def get_html(self, url="", path="", repeated=False):
    '''
    '''
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
  '''
  '''

  def __init__(self):
    '''
    '''
    self.subprocesses_list = []
    self.pending_lst = []
    self.max = 4
    self.output = ''

  def hide_console(self):
    '''
    '''
    startupinfo = None
    if os.name == 'nt':
      startupinfo = subprocess.STARTUPINFO()
      startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    return startupinfo
    
  def run(self, cmd, cwd=''):
    '''
    '''
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
    return trace
      
  def trace_console(self, p):
    '''
    '''
    output = ""
    try:
      for line in iter(p.stdout.readline, b''):
        output += line.rstrip().decode('utf-8')+'\n'
    except ValueError:
      print('subprocess stopped.')
    return self.escape_password(output)

  def escape_password(self, output):
    '''
    '''
    if 'git push' not in output:
      return output
    return output.replace(output[output.rfind(":")+1:output.find("@")],
                          "********")

sp = subprocesses()

#---/ MPAT functions /---------------------------------------------------------
#
class annotation_functions(common_functions):
  """
  Contains Morphology Pre-annotation Tool workflow functions.
  """

  GIT_MPAT = 'git+https://github.com/cdli-gh/' \
             'morphology-pre-annotation-tool.git'
  GIT_ANNOTATED = 'https://github.com/cdli-gh/mtaac_gold_corpus.git'
  ANNOTATED_ROOT = os.path.join(BASE_DIR, "data")
  ANNOTATED_REPO_NAME = 'mtaac_gold_corpus'
  ANNOTATED_PATH = os.path.join(ANNOTATED_ROOT, ANNOTATED_REPO_NAME)
  TO_ANNOTATE = os.path.join(ANNOTATED_PATH, 'morph', 'to_annotate')
  TO_DICT = os.path.join(ANNOTATED_PATH, 'morph', 'to_dict')
  PROCESSED = os.path.join(ANNOTATED_PATH, 'morph', 'processed')
  progress_json_path = os.path.join(ANNOTATED_PATH, 'morph', 'progress.json')
  
  def __init__(self, username, password, production_mode=True,
               branch='workflow'):
    '''
    The `production_mode` parameter, when True, allows Github upadates.
    '''
    self.branch = branch
    self.production_mode = production_mode
    self.user = username
    self.password = password
    self.actualize()

  def actualize(self):
    '''
    Actualize MPAT and annotated data.
    Correct format of downloaded files, if needed.
    '''
    self.install_or_upgrade_mpat()
    if not os.path.exists(self.ANNOTATED_ROOT):
      os.makedirs(self.ANNOTATED_ROOT)
    if not os.path.exists(os.path.join(self.ANNOTATED_ROOT,
                                       self.ANNOTATED_REPO_NAME)):
      self.clone_annotated()
    else:
      self.update_annotated()
    IDs_lst = [f.split('.')[0] for f in os.listdir(self.TO_DICT)]
    self.correct_format(IDs_lst, dir_path=self.TO_DICT)
    self.load_progress_data()

  #---/ MPAT functions /-------------------------------------------------------
  #
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

  #---/ Progress data /--------------------------------------------------------
  #
  def load_progress_data(self, path=''):
    '''
    Load `self.progress_dict` from JSON, when exists,
    or create it as blank dict. Dict. format:
    {'username': {annotating: P00003, done: [P00001, P00002]}
    '''
    if not path:
      path = self.progress_json_path
    if hasattr(self, 'progress_dict'):
      if os.path.exists(path):
        self.import_and_merge_progress_data(path)
    elif os.path.exists(path):
      self.progress_dict = self.load_json(path)
    else:
      self.progress_dict = {}
    self.progress_lst = []
    for k in self.progress_dict.keys():
      if self.progress_dict[k]['annotating']!='':
        self.progress_lst.append(self.progress_dict[k]['annotating'])
      self.progress_lst+=self.progress_dict[k]['done']

  def import_and_merge_progress_data(self, path):
    '''
    Import and merge progress data from an outer source.
    E.g. when the remote progress file was updated.
    '''
    pd = self.load_json(path)
    if pd!=self.progress_dict:
      for k in pd.keys():
        if k!=self.user:
          self.progress_dict[k] = pd[k]

  def progress_data_annotating_update(self, ID):
    '''
    Add new ID to `self.progress_dict` and `self.progress_lst`.
    Then dump `self.progress_lst` to JSON.
    '''
    self.progress_lst.append(ID)
    if self.user not in self.progress_dict.keys():
     self.progress_dict[self.user] = {'annotating': '', 'done': []}
    self.progress_dict[self.user]['annotating'] = ID
    self.update_progress_data(remote=True)

  def progress_data_ready_update(self):
    '''
    Move annotated ID to "done" list in `self.progress_dict`.
    Then dump `self.progress_lst` to JSON.
    '''
    ID = self.progress_dict[self.user]['annotating']
    self.progress_dict[self.user]['done'].append(ID)
    self.progress_dict[self.user]['annotating'] = ''
    self.update_progress_data(remote=True)

  def update_progress_data(self, remote=False):
    '''
    Dump `self.progress_lst` to JSON.  
    '''
    if remote:
      # ToDo: update progress.json here!
      self.fetch_file('morph/progress.json')
      self.load_progress_data()
    self.dump(json.dumps(self.progress_dict), self.progress_json_path)

  #---/ Select and preannotate new text /--------------------------------------
  #
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

  #----/ Push annotated text to repo /-----------------------------------------
  #
  def correct_and_push(self):
    '''
    Push text workflow:
    1. Run mpat with -f switch to correct the format.
    2. Update `self.progress_dict`.
    3. Move .conll file from `self.PROCESSED` to `self.TO_DICT`
    4. Push changes to repo.
    '''
    self.actualize()
    ID = self.progress_dict[self.user]['annotating']
    self.correct_format([ID])
    target = os.path.join(self.PROCESSED, '%s.conll' %ID)
    dest = os.path.join(self.TO_DICT, '%s.conll' %ID)
    shutil.move(target, dest)
    self.progress_data_ready_update()
    git_message = 'Add annotated %s.conll by %s' %(ID, self.user)
    self.update_github(git_message)

  #----/ Checks and corrections /----------------------------------------------
  #
  def correct_format(self, IDs_lst=[], dir_path=''):
    '''
    For each file from a list of IDs in dir_path (default is self.PROCESSED):
    1. run `self.csv2tsv()`: convert CSV to TSV. 
    2. Run mpat with -f switch to correct the file format:
      2a. remove extra columns and
      2b. add underscores in empty cells.
      2c. Then replace the original with it.
    3. Print report on csv2tsv cases.
    '''
    if not dir_path:
      dir_path = self.PROCESSED
    if not IDs_lst:
      IDs_lst = [self.progress_dict[self.user]['annotating']]
    invalid_uft8_count = 0
    csv2tsv_count = 0
    for ID in IDs_lst:
      file_path = os.path.join(dir_path, '%s.conll' %ID)
      if self.correct_unicode(file_path):
        print('Corrected invalid unicode: %s' %ID)
        invalid_uft8_count+=1
      if self.csv2tsv(file_path):
        print('Corrected CSV: %s' %ID)
        csv2tsv_count+=1
      output_path = os.path.join(dir_path, 'output', '%s.conll' %ID)
    print('Correcting format in %s file(s).'
          '\n\tInvalid UTF-8: %s file(s)'
          '\n\tCSV > TSV: %s file(s).'
          %(len(IDs_lst),
            invalid_uft8_count,
            csv2tsv_count))
    # the following can probably be removed,
    # as it's functionality is duplicated by the lines above,
    # but is less reliable:
    sp.run(['mpat', '-f', '-i', dir_path])
    shutil.move(output_path, file_path)
    shutil.rmtree(os.path.join(dir_path, 'output'))

  def correct_unicode(self, path):
    '''
    Check if valid Unicode, convert from ANSI, if needed.
    Subfunction of ´self.correct_format()´.
    '''
    with codecs.open(path, 'r', 'utf-8') as f:
      try:
        conll_lines = f.readlines()
        return False
      except UnicodeDecodeError:
        pass
    with codecs.open(path, 'r', 'ansi') as f:
      f_str = str(f.read())
    self.dump(f_str, path)      
    return True
      
  def csv2tsv(self, path):
    '''
    WARNING: This function clears the content of the last 3 columns.
    Convert CST to TSV.
    Also:
      - Remove extra tabs rests.
      - Insert '_' to empty fields.
    Subfunction of ´self.correct_format()´.
    '''
    with codecs.open(path, 'r', 'utf-8') as f:
      conll_lines = list(f.readlines())
      if ',' not in ''.join(conll_lines):
        return False
      conll_lines = [l.strip('\r\n') for l in conll_lines]
      if conll_lines==[]:
        return False
    tsv_str = ''
    for csv_row in conll_lines:
      if '#' in csv_row:
        csv_row = csv_row.strip(',')
      else:
        columns = []
        for cell in [c.strip('\t_') for c in csv_row.split(',')[:4]]:
          if cell=='':
            cell = '_'
          columns.append(cell)
        csv_row = ','.join(columns+['_' for i in range(0,3)])
      tsv_row = csv_row.replace(',', '\t') #'\t'.join(csv_row.split(','))
      tsv_str+=tsv_row+'\n'
    self.dump(tsv_str[:-1], path)
    return True

  def check_for_errors(self):
    '''
    Check annotated text for errors with mpat.
    '''
    ID = self.progress_dict[self.user]['annotating']
    file_path = os.path.join(self.PROCESSED, '%s.conll' %ID)
    return sp.run(['mpat', '-c', '-i', file_path])

  #---/ Git functions /--------------------------------------------------------
  #
  def update_github(self, message):
    '''
    Push repo to GitHub if `self.production_mode` is True.
    '''
    if self.production_mode:
      repo_data = 'https://%s:%s@%s' %(self.user,
                                       self.password,
                                       self.GIT_ANNOTATED.split('//')[1])
      # Use ['git', 'checkout', '-b', self.branch] to create branch
      sp.run(['git', 'checkout', self.branch], cwd=self.ANNOTATED_PATH)
      sp.run(['git', 'add', '.'], cwd=self.ANNOTATED_PATH)
      sp.run(['git', 'commit', '-a','-m', message], cwd=self.ANNOTATED_PATH)
      sp.run(['git', 'push', repo_data, self.branch],
             cwd=self.ANNOTATED_PATH)

  def fetch_file(self, path):
    '''
    Fetch a single remote file.
    '''
    sp.run(['git', 'fetch'], cwd=self.ANNOTATED_PATH)
    sp.run(['git', 'checkout', self.branch, '--', path],
           cwd=self.ANNOTATED_PATH)

#    
#---/ Dashboard scripts /------------------------------------------------------
#
class Dashboard(common_functions):
  '''
  '''

  def __init__(self, production_mode=True):
    '''
    '''
    self.production_mode = production_mode
    self.primary = True

  def login_view(self):
    '''
    '''
    self.templates_manager("login", {})

  def new_text_view(self):
    '''
    '''
    self.templates_manager("new_text",
                           {"username": self.login_data['username']})

  def annotation_view(self):
    '''
    '''
    ID = self.af.progress_dict[self.af.user]['annotating']
    self.templates_manager("annotate",
                           {"username": self.login_data['username'],
                            "textID": ID})
    
  def annotation_status_check(self):
    '''
    '''
    if self.af.user not in self.af.progress_dict.keys():
      return 'add new'
    elif self.af.progress_dict[self.af.user]['annotating']=='':
      return 'add new'
    return 'annotate'

  def github_login_check(self, username, password):
    '''
    '''
    try:
      g = Github(username, password)
      repos_lst = [x.full_name for x in g.get_user().get_repos()]
      if 'cdli-gh/mtaac_gold_corpus' in repos_lst:
        return True
      return None
    except GithubException as e:
      return False

  def github_login(self, json_data, branch='workflow'):
    '''
    '''
    login_data = json.loads(json_data)
    login_check = self.github_login_check(login_data["username"],
                                          login_data["password"])
    if login_check in [None, False]:
      eel.login_error()
    else:
      self.login_data = login_data
      self.plug_annotation_backend(branch=branch)
      status = self.annotation_status_check()
      if status=='add new':
        self.new_text_view()
      elif status=='annotate':
        self.annotation_view()
  
  def plug_annotation_backend(self, branch='workflow'):
    '''
    '''
    self.af = annotation_functions(self.login_data["username"],
                                   self.login_data["password"],
                                   production_mode=self.production_mode,
                                   branch=branch)

  def select_new_text(self):
    '''
    '''
    self.af.update_mpat_dict()
    self.af.select_new_text()
    self.annotation_view()

  def check_for_errors(self):
    '''
    '''
    errs = self.af.check_for_errors()
    errs_html_str = ''
    for err in errs.strip('\n').split('\n\n'):
      err = err.strip(" ")
      if len(err)!=0:
        errs_html_str+='''<li class="list-group-item ''' \
                        '''list-group-item-danger">%s</li>''' %err
    if len(errs_html_str)==0:
      return None
    return "<ul class='list-group'>%s</ul>" %errs_html_str

  def correct_and_check(self):
    '''
    '''
    self.af.correct_format()
    
  def correct_and_push(self):
    '''
    '''
    self.af.correct_and_push()
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
    '''
    '''
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
    '''
    '''
    ID = self.af.progress_dict[self.af.user]['annotating']
    url = "https://cdli.ucla.edu/search/archival_view.php?ObjectID=%s" %ID
    webbrowser.open(url)
#
#---/ Variables /--------------------------------------------------------------
#
# Use `git_branch` to override the default 'workflow' git repo branch.
git_branch = 'workflow'
#
# Use `production_mode=False` while testing to skip Github updates.
production_mode = True
#
#---/ Eel functions /----------------------------------------------------------
#
eel.init('static')
d = Dashboard(production_mode=production_mode)

@eel.expose
def github_login(json_data):
  '''
  '''
  print('check github login data')
  d.github_login(json_data, branch=git_branch)    

@eel.expose
def select_new_text():
  '''
  '''
  print('selecting new text')
  d.select_new_text()

@eel.expose
def correct_and_check():
  '''
  '''
  print('correcting and checking')
  d.correct_and_check()
  
@eel.expose
def correct_and_push():
  '''
  '''
  print('converting and pushing')
  d.correct_and_push()

@eel.expose
def check_for_errors():
  '''
  '''
  print('checking for errors')
  errors = d.check_for_errors()
  if errors==None:
    return "clean"
  else:
    return errors

@eel.expose
def open_dir():
  '''
  '''
  print('opening directory')
  d.open_dir()
  
@eel.expose
def open_page():
  '''
  '''
  print('opening web page')
  d.open_page()

#---/ Main /-------------------------------------------------------------------
#
if __name__ == "__main__":
  '''
  '''
  if platform.system()=='Windows' and "HOME" not in os.environ.keys():
    os.environ["HOME"] = os.environ["USERPROFILE"]
  d.login_view()



