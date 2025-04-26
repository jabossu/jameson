import subprocess
import datetime
import shlex
import cfg
from modules.MyModules import *

def commit(message=None):
    print("✅", "Saving changes...")
    message = str(message)
    if len(message) == 0:
        print("WARNING: Commit message cannot be empty")
        message = dadatetime.dadatetime.now().isoformat(timespec='minutes')
    
    if cfg.dry_run:
        d = "--dry-run" 
        print("⚠️ ", "Running Git in dry-run mode")
    else:
        d = ""
    
    commands = ('git add {} --all'.format(d), 'git commit {} -m "{}"'.format(d, message))
    
    for c in commands:
        echo( "Running command", shlex.split( c ) )
        
        r = subprocess.run(
            shlex.split( c ),
            cwd=cfg.v['root'],
            stdout=subprocess.PIPE
            )
            
def push():
    print("⏫","Uploading changes...")
    if cfg.dry_run:
        d = "--dry-run" 
        print("⚠️ ", "Running Git in dry-run mode")
    else:
        d = ""
    
    commands = ('git checkout {}'.format(cfg.v['branch_main']),
                'git merge {}'.format(cfg.v['branch_working']),
                'git push origin --all {}'.format(d),
                'git checkout {}'.format(cfg.v['branch_working'])
                )
    
    for c in commands:
        echo( "Running command", shlex.split( c ) )
        
        subprocess.run(
            shlex.split( c ),
            cwd=cfg.v['root']
            )
        
def sync():
    print("♻️","Syncing changes...")
    print ("⛔", "not implemented")
