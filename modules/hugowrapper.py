import subprocess, shlex, re, pathlib
import cfg
import modules.gitwrapper as gitwrapper
from modules.MyClasses import *


def new_post(keyword):
    """Call onto HUGO to create a new post"""
    
    try:
        # the string can be either "archetype/title" or "title" 
        # If there is an archetype, extract it.
        # if there is not, it will raise a TypeError because re.search()[2] will be None
        # we'll except for it later on
        regex = r"(.*)/(.*)"
        archetype = re.search(regex, keyword)[1]
        title = re.search(regex, keyword)[2]
        post_filepath = "/".join( ('content/posts', archetype, normalize(title) ) )
        
        archetype_filepath =  pathlib.Path( '{}/archetypes/{}.md'.format(cfg.v['root'], archetype) )
        
        # we check that the archetype actually exists.
        if not archetype_filepath.is_file():
            print('⛔','Post archetype "{}" not found !'.format(archetype) )
            print_line()
            # It doesn't ! let's recap which archetype are valid for the user.
            print('Available archetypes are :') 
            for k,i in enumerate( archetype_filepath.parents[0].iterdir() ):
                j = pathlib.Path(i)
                print('{:>3}.  {}'.format(k+1, j.stem))
            print_line()
            exit(1) #we exit so the user can try again
        
    except TypeError:
        #  if there is no archetype, TypeError will be raised.
        title = keyword
        archetype = ""
        post_filepath = "/".join( ('content/posts', normalize(title) ) )
    post_filepath += '.md'
    
    print('✍️ ', 'Creating new post: "{}" at {}'.format(title,post_filepath) )
    command = 'hugo new "{}" '.format(post_filepath)
    # we have to tell hugo to use the archetype, if set
    if archetype:
        command += '--kind {}'.format(archetype)
    
    # run command
    r = subprocess.run( shlex.split(command), cwd=cfg.v['root'], stdout=subprocess.PIPE, text=True )
    # let's check if everything resolved.
    # Hugo doesnt user stderr, but prints "error" in stdout. 
    # let's catch it
    if 'Error' in r.stdout:
        print('⛔', r.stdout.strip())
        #exit(1)
    else:
        print('✅', r.stdout.strip())
    
    # now that the file.md is created, we can load it.
    p = post( post_filepath )
    edit( p.filepath )
    p.reload() # we reload metatdatas
    
    # we commit
    gitwrapper.commit('New post: {}'.format(p.metadatas['title']) )
