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
            
            pl = post_list( filters )
            # check how many post we got from filters.
            # cannot be 0 as it was checked earlier.
            num_posts = len( pl.list() )
            
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
