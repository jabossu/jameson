import yaml, re, subprocess, shlex, pathlib, datetime
import cfg
from modules.MyModules import *

class post:
    def __init__(self, filepath):
        """Open a file and populate metadatas and content from it"""
        filepath = fullpath(filepath)
        self.filepath = pathlib.Path( filepath )
              
        try:
            with self.filepath.open( ) as file:
                text = file.read()
        except FileNotFoundError:
            print('⛔', 'Error: "{}" doesn\'t exist'.format(self.filepath.absolute() ) )
            exit(1)
        
        regex = "---\n(.+?)\n---\n(.*)"
        ### (.+?) catches the SHOREST string between the FIRST of two --- instances
        ### (.*) catches all the rest AFTER the SECOND ---
        result = re.search( regex, text, re.DOTALL )   
        self.metadatas = yaml.safe_load( result[1] )
        self.content = result[2]
        
    def title(self):
        return( normalize(self.metadatas['title'])) 
        
    def get(self, displayFull=False):
        """Return Object content formatted for Hugo"""
        if displayFull:
            r = '-'*3 +'\n'
        else:
            r = '—'*70 +'\n'
            
        for i in self.metadatas:
            
            # the metadata is a data block
            if ']' in str(self.metadatas[i]):
                r += "{}:\n".format(i)
                for k in self.metadatas[i]:
                    r += " - {}\n".format(k) 
            
            # the metadata is on several lines
            elif '}' in str(self.metadatas[i]):
                r += "{}:\n".format(i)
                for k in self.metadatas[i]:
                    r += ' {}: "{}"\n'.format(k.strip() , self.metadatas[i][k]) 
            
            # the metadata is on one line 
            else:
                if isinstance( self.metadatas[i], bool):
                    r += '{}: {}\n'.format(i, self.metadatas[i]) 
                else:
                    r += '{}: "{}"\n'.format(i, self.metadatas[i]) 
        
        if displayFull:
            r += '-'*3 +'\n'
        else:
            r +='\n>>> '
            
        if displayFull:
            r += self.content.strip()
        else:
            r += "{} [...] {}".format(self.content[0:30], self.content[-20:-1]).strip()
        
        return r
        
    def edit(self):
        now = datetime.date.today().strftime('%Y-%m-%d')
        if self.metadatas['draft']:
            self.metadatas['date'] = now
        elif self.metadatas['date'] != now:
            self.metadatas['lastmod'] = now
            
        self.save()
        self.reload()
        edit( self.filepath )
        
    def reload(self):
        with open( self.filepath, "r") as file:
            text = file.read()        
        regex = "---\n(.+?)\n---\n(.*)"
        ### (.+?) catches the SHOREST string between the FIRST of two --- instances
        ### (.*) catches all the rest AFTER the SECOND ---
        result = re.search( regex, text, re.DOTALL )   
        self.metadatas = yaml.safe_load( result[1] )
        self.content = result[2]
    
    def save(self):
        """Output Object to self.filepath"""
        with open( self.filepath, 'w' ) as file:
            file.write( self.get(displayFull=True) )
            
    def delete(self):
        pathlib.Path( fullpath( self.filepath) ).unlink()
            
    
    def print(self, displayFull=False):
        print( self.get(displayFull) )


class filter_list(list):
    def __init__( self, argv ):
        echo('Building filter_list')
        self.list = list()
        if "--all" in argv:
            self.mode = 'all'
        elif "--any" in argv:
            self.mode = "any"
        else:
            self.mode = "all"
            
        self.params_used = list() # we'll use this to remove already used parameters
        
        for k, arg in enumerate( argv ):
            if arg == '-f':
                try:
                    regex= r"(\w+):(\w+)" 
                    pair = argv[k+1]
                    (key, value) = (re.search( regex, pair )[1], re.search( regex, pair )[2])

                except IndexError:
                    print( 'no args' ) # there was nothing after the -f parameter
                except TypeError:
                    print( 'invalid filter' ) #the filter didnt match the regex
                else:
                    # we got the filters from the arguments
                    # we will remove -f and it's parameter later.
                    self.params_used.append(k)
                    self.params_used.append(k+1)
                    self.list.append( (key, value) )


class post_list(list):
    
    def __init__(self, filters ):
        """Build a list of posts objects, using filters and filter mode"""
        echo("search with", filters.list)
        # Filters are a list( key, value )
        # Keys can be filepath, content, or any tag
        # somes values are not strings, but list or dictionnaries
        # such values are linked to keys tags, categories, series, and image
        
        if filters.mode not in ("all", "any"):
            print( "invalid mode for filtering" )
            exit(1)
        echo('Filtering mode:', filters.mode)
        
        # Generate full list of all posts filepaths
        c = subprocess.run( 
            shlex.split( 'find content/ -name "*.md"' ),
            stdout = subprocess.PIPE, text=True,
            cwd = cfg.v['root'] 
        ).stdout.rstrip().splitlines()    
        
        # for each post, we load it into a post object
        full_list = list()
        for i in c:
            full_list.append( post(i) )
        
        self.total_num_posts = len(full_list)
        
        # now we filter the post list to the user's request
        match filters.mode:
        
            case "all": # the article must match ALL filters to be kept
                result_list = full_list
                removelist = list()
                for i in filters.list: # i[0] is key, i[1] is value
                    for k, j in enumerate(result_list):
                    
                        if i[0] == 'file' and not normalize(i[1]) in normalize(j.filepath):
                            echo('remove file', j.filepath)
                            if k not in removelist:
                                removelist.append( k )
                            
                        elif i[0] == 'content' and not " {} ".format(normalize(i[1])) in normalize(j.content):
                            echo('remove content from', j.filepath)
                            if k not in removelist:
                                removelist.append( k )
                        
                        elif i[0] in j.metadatas:
                            if not normalize(i[1]) in normalize(j.metadatas[i[0]]):
                                echo('remove with tag from', j.filepath)
                                if k not in removelist:
                                    removelist.append( k )
                        else:
                            echo('not filtered', j.title() )
                            if k not in removelist:
                                removelist.append( k )
                
                removelist.sort()
                removelist.reverse()
                for i in removelist:
                    try:
                        del result_list[i]
                    except IndexError:
                        print(len(result_list), k)
            
            case "any": # the post must match any filter to be returned
                result_list = list()
                for i in filters.list: # i[0] is key, i[1] is value
                    for j in full_list:
                    
                        if i[0] == 'file' and normalize(i[1]) in normalize(j.filepath):
                            echo('add file', j.filepath)
                            if not j in result_list:
                                result_list.append( j )
                            
                        elif i[0] == 'content' and " {} ".format(normalize(i[1])) in normalize(j.content):
                            echo('add content from', j.filepath)
                            if not j in result_list:
                                result_list.append( j )
                        
                        elif i[0] in j.metadatas and normalize(i[1]) in normalize(j.metadatas[i[0]]):
                            echo('add with tag from', j.filepath)
                            if not j in result_list:
                                result_list.append( j )
                            
        self._list = sorted(result_list, key=post.title)
        self.num_posts = len(result_list)
        
        if self.num_posts == 0:
            print('☠️ ', 'No post match given filters. Try adding "--any".')
            exit(1)
        else:
            plural = "s" if self.num_posts >= 2 else ""
            print('🔎', 'Found {}/{} matching post{}'.format(self.num_posts, self.total_num_posts, plural) )
        
    def list(self):
        return( self._list )
    
    def print(self):
                
        for k, i in enumerate(self._list):
            try:
                date = i.metadatas['date']
            except KeyError: # some pages don't have a date.
                date = ".........."
                
            print("{: >4}. [{}]  {}".format( k+1, date , i.metadatas['title'] ) )
            k+=1
