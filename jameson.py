#! /bin/python3

##==========================================
## Jameson, the friendly helper for Hugo (gohugo.io)
## (named after J. Jonah Jameson)
##
## this is a rewrite in python.
##
##  written by jabossu under GPL3
##==========================================

version="2-beta.O"

# === MODULE IMPORT ===
import yaml, shlex, re
from subprocess import run, DEVNULL
from sys import argv

import modules.gitwrapper as gitwrapper
import modules.hugowrapper as hugowrapper
from modules.MyModules import *

# === CLASS IMPORT ===
from modules.MyClasses import *


# ——————————————————————————————————————————————
# === LOAD CONFIG ===
import cfg

## BUILD FILTER LIST
filters = filter_list( argv )

# to preserve the indexes, we will remove items from end to start
filters.params_used.reverse() 
for i in filters.params_used:
    del argv[i]

# ——————————————————————————————————————————————
## MAIN LOOP

for i, argument in enumerate(argv): 
    
    # We'll process arguments one by one
    match argument:
    
        case "new":
            try:
                hugowrapper.new_post( argv[i+1] )
            except IndexError:
                print('⛔', 'New post needs a name !')
                exit(1)
            exit(0)
    
        case "list":
            ## If search mode is activated
            # search by title : -t <TITLE>
            # search by metadata : -m <META>=<VALUE>
            
            pl = post_list( filters )
            pl.print()
            
            # command completed, EXIT
            exit(0)
        
        case "show":
            pl = post_list( filters )
            for i in pl.list():
                i.print()
            exit(0)
        
        case "drafts":
            print("Searching for drafts...")
            filters.list.append( ('draft', 'True') )
            pl = post_list( filters )
            pl.print()
            exit(0)
       
        case "edit":
            
            # If there is another argument passed that is not an option flag 
            # (option flag contain "-" : --all, -d...)
            # assume the user is using a shortcut and giving us a title.
            # Rebuild the filters accordingly and search from it.
            try:
                if '-' not in argv[i+1]:
                    shortcut_mode = True
                    filters.list.extend( 
                            filter_list( ('-f', "title:{}".format(argv[i+1]) )).list
                        ) # we add a new filter with title
                else:
                    shortcut_mode = False
            except IndexError:
                shortcut_mode = False
            
            pl = post_list( filters )   # exit(1) if 0 match
            num_posts = len(pl.list())  # so it can only be >= 0
            
            if shortcut_mode and num_posts !=1:
                # shortcut modes can only be used if there is one valid result
                # it's to be used in graphical launchers
                print('Too many posts match this title. Try again')
                exit(1)            
            
            if num_posts == 1:
                # if the is only one, we edit it.
                p = pl.list()[0]
                print('✅', 'Matching post found: "{}"'.format( p.metadatas['title']))
                p.edit()
                
            elif num_posts > 1:
                # if there are more, we let user choose between
                # edit one or edit all, one by one
                
                # let's display a list
                print_line()
                print('ℹ️ ', "Several posts found matching filters :")
                pl.print()
                print_line()
                
                # we ask user choice
                try:
                    print('👉', "Choose which to edit")
                    choice = input("(1-{} / 0 for all): ".format(num_posts))
                except KeyboardInterrupt: # user can quit with ctrl-C,
                    print('\nUser interrupt. Goodbye') 
                    exit(1)
                
                try:
                    # we can only accept integers between 1 and the number of posts we got.
                    choice = int(choice) 
                    if choice > num_posts:
                        raise ValueError()
                except (ValueError, TypeError):
                    print("Not a valid number. Exiting.")
                    exit(1)
                    # we exit gracefully if user choice isnt a valid number
                
                if choice == 0:
                    # the user wants to edit each and every file
                    for k, i in enumerate( pl.list() ):
                        try: # We'll catch a ctrl-C and exit.
                            print_line()
                            print( '[{}/{}] Editing "{}"'.format(k+1, num_posts, i.metadatas['title']) )
                            i.edit() 
                        except KeyboardInterrupt:
                            print('\nQuit')
                            exit(0)    
                else: # the user chose a file to edit.
                    # we have to substract 1 to get a valid index 
                    pl.list()[choice-1].edit()
            # command completed, EXIT
            exit(0)
        
        case "metaedit":
            # we want to edit/update/remove metadatas in bulk on filtered posts
            

            
            # Loop through arguments
            new_metas = list()
            for i in argv:
                ## commands can be as follow :
                #   jameson metaedit title="newtitle"   : set metadatas to new value
                #   jameson metaedit tags+"newtag"      :   add metadatas value to a list
                #                                           if not list, wee concatenate the strings
                #                                           if None, we replace
                #   jameson metaedit tags-"oldtag"      : remove metadata value from a list
                    
                regex = r"([\w ]+)([+=-])([\w ]*)"
                try:
                    r = re.search(regex, i)
                    
                    if isinstance(r, type(None)):
                        raise KeyError
                    
                    key = r[1]
                    value = r[3]
                    match r[2]:
                        case '+':
                            mode = 'add'
                        case '=':
                            mode = 'set'
                            filters.list.append( (key, value) )
                        case '-':
                            mode = 'remove'
                            filters.list.append( (key, value) )
                    
                    print('✍️ ', 'Editing metadata : for [{}], {} "{}"'.format(
                        key, mode, value
                        ))
                    
                    new_metas.append( {'key': key, 'value':value, 'mode': mode} )
                    
                    
                    
                except KeyError:
                    # if argument does not patch the pattern, do nothing
                    pass
            
            ## We load posts to metaedit
            pl = post_list( filters )
            
            # we now process the edits, WITHOUT saving them
            for p in pl.list():
                p.metaedit( new_metas ) 
            
            # Now we ask for user confirmation
            try:
                confirm = input('\n❓ Apply changes ? (yes/No) ').casefold()
                while not confirm in ('yes', 'no') :
                    confirm = input('Please answer with "yes" or "no" : ').casefold()
            except KeyboardInterrupt:
                print('\nQuit')
                exit(1)
            
            if confirm == 'yes':
                for p in pl.list():
                    p.save()
            
            exit(0) # everything wen fine, we exit
        
        case "import":
            if "-k" in argv or "--keep" in argv:
                keep_sourcefile=True
            else:
                keep_sourcefile=False
                
            try:
                print( 'Importing "{}"'.format(argv[i+1]) )
                import_image( argv[i+1], keep_sourcefile )
            except IndexError:
                print("⛔", "No file given in arguments")
                exit(1)
            
            exit(0)
            
        case "config":
            # we display the config parameters
            for i in cfg.v:
                print(" · {:<15}: {}".format(i, cfg.v[i]))
            print('To edit, pass "-e" as argument')
            if '-e' in argv: # user wants to edit the file
                cfg.edit( cfg.v['editor'], cfg.config_file.absolute(), ask="y")
            exit(0)
                
        case "save":
            gitwrapper.commit("Saved changes")
            if "publish" in argv:
                gitwrapper.push()
            exit(0)
        case "publish":
            gitwrapper.push()
            exit(0)
        case "sync":
            gitwrapper.sync()
            exit(0)
        
        case "help":
            cfg.help()
            exit(0)
        
print('No argument was recognised. Use "jameson help"')
exit(1)
