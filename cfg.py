import yaml
from sys import argv
import platformdirs
import pathlib
import subprocess 
import shlex

def echo( *text ):
    """Outputs text, only if verbose mode is active"""
    ### This is a duplicate from MyModules.py that i cannot import.
    if verbose_mode:
        print( str(text) )

def edit(editor, config_file, ask=True):
    if editor != "": # If we know a valid editor, allow the user to edit configfile
        print(ask)
        if ask == True:
            user_choice = input("Would you like to edit it [y/N] ? ")
        else:
            user_choice = ask
        if user_choice.casefold() == "y":
            echo('Editing config file', config_file.absolute(), 'with', editor)
            command = shlex.split( editor )
            command.append( config_file.absolute() )
            
            subprocess.run( 
                command, stderr=subprocess.DEVNULL )
    else:
        echo('Editor not set')

# ———————————————————————————————————————————————————————————————————————————

# define verbosity
global verbose_mode
verbose_mode = False
if '-v' in argv:
    verbose_mode = True
    del argv[ argv.index('-v') ]

# check for dry-runs
global dry_run
dry_run = True
print('👀', "Turning dry-run mode on. I'm in cfg.py line43")
for i in ('-n', '--no', '--dry-run'):
    if i in argv:
        dry_run = True
        del argv[ argv.index( i ) ]

# ———————————————————————————————————————————————————————————————————————————

# We'll use this int() to check if everything went fine at the end.
error = 0

# LOAD CONFIG FILE
appname="jameson"
config_dir = pathlib.Path( platformdirs.user_config_dir(appname) )
config_file = pathlib.Path( '{}/config.yaml'.format( config_dir ) )

## Check whether config file exists
## If not, we'll create them and populate with default settings
if not config_file.is_file( ):
    print("Config file doesn't exist")
      
    default_config = {
        'root': None,
        'branch_main': 'main',
        'branch_working': 'writting'
        }

    for i in ('yolo', 'nano', 'emacs', 'vim'):
        e = subprocess.run( ("which", i), stdout = subprocess.PIPE, text=True, stderr=subprocess.DEVNULL ).stdout.strip()
        if e != '':
            default_config['editor'] = e
            break
            
            
    if not config_dir.is_dir():
        echo("Config directory doesn't exist")
        config_dir.mkdir(parents=True)
        config_file.touch()
        
    with config_file.open(mode='w') as f:
        f.write( yaml.dump( default_config ) )
    
    print('Configuration has been created. However, you have to edit it and add the root of you Hugo project.')
    print('You can find you config file in {}'.format(config_file.absolute()) )
    error += 1


# ———————————————————————————————————————————————————————————————————————————
# VERIFY CONFIGURATION VALIDITY 
global config
with config_file.open( ) as f:    
    v = yaml.safe_load( f ) 
    
## Check if configuration is valid :
### Check if root is a valid directory
if not pathlib.Path( str( v['root'] ) ).is_dir():
    error += 1
### Check if editor is a valid command
editor = subprocess.run( ("which", v['editor'].split()[0]), stdout = subprocess.PIPE, text=True, stderr=subprocess.DEVNULL ).stdout.strip()
if editor == "":
    print(editor, v['editor'])
    error += 1
### Check if branches are set. Set them otherwise 
if not isinstance(v['branch_main'], str):
    print('branch_main is not configured. Usind "main" as default')
    v['branch_main'] = "main"
if not isinstance(v['branch_working'], str):
    print('branch_working is not configured. Usind "writting" as default')
    v['branch_working'] = "writting"

if error > 0:
    print('Config file is not valid')
    
    edit(v['editor'], config_file)
    
    exit(1) # We exit, as config is not valid.
else:
    echo('Valid config file {} loaded'.format(config_file.absolute()) )
