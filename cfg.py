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
dry_run = False
if dry_run:
    print('👀', "Turning dry-run mode on by default. I'm in cfg.py line 42")
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

# ———————————————————————————————————————————————————————————————————————————
# Help command
def help():
    print("""#===================
Jameson, the fantastic editor for hugo blogging. 
    
# FILTERING
#===================
Jameson use filters to grant finer control on which post it should work on.
Filters can be provided in any position of argument.
Filters can be specified with "-f property:value"
    Property can be :
    - file      : to search from filenames
    - content   : to search for the "value" in the content of a post
    - other     : to search metadatas for a metadata name "other" that has the value "value".
                  ie: tags:voyage, categories=opinion, date=2023-12-31 ...

By default, only posts matching ALL filters will be returned. (--all)
You can select all posts matching ANY filter by passing "--any" as an argument.


# CONTENT MANAGEMENT
#===================
    new <title> :   create a new post with title.
    
    list        :   show a list of matching posts. Can be used with filters
        
    show        :   display extract of matching posts. can be used with filters.
        
    drafts      :   lists drafts. can be used with filters.
       
    edit        :   edit matching posts.
                    use with filters for finer control.
    
    
    metaedit    :   edit metadatas in bulk. Several modes of operation.
                    several modes can be used at the same time.
                    
    metaedit <property+value> : add mode
                    add "value" to the property. 
                    Use in combination with filters for finer control
                    WILL prompt user for confirmation before editing textfiles
    metaedit <property-value> : remove mode
                    remove "value" to the property. 
                    Will only target posts that actually have this property and this value.
                    Use in combination with more filters for finer control
                    WILL prompt user for confirmation before editing textfiles
    metaedit <property=value> : set mode
                    Set property to "value".
                    Use in combination with more filters for finer control
                    WILL prompt user for confirmation before editing textfiles
                    
        
    import  <path/to/img> :
                    import image, converting it to WEBP format for reduced size
                    and placing it into /static/img/pictures/YYYY-MM/image.webp.
                    Also générates -thumb thumbnail
                    Also strips exif metadatas for privacy
                    Also removes sourcefile
                    Also copy the filepath to clipboard
            --keep | -k :
                    Keep sourcefile, not removing it.


        
# VERSION MANAGEMENT
#===================
    save        :   use Git to commit changes
    publish     :   use Git to push to remote
    sync        :   use Git to pull & push from origin, syncing with remote repo.  

# OTHER
#===================
    help        :   This help

    config      :   print out config file values
            -e  :   edit config file in editor

""")
