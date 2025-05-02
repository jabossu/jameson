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
            r += 'file: {}\n'.format( str(self.filepath.relative_to(cfg.v['root']) ) )
            
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
    
    def metaedit(self, new_metas):
        """Add, remove, or update metadatas of post with given arguments"""
            
        print("\n  {}".format(self.filepath.relative_to(cfg.v['root'])))
        datas_before=dict()
        datas_after=dict()
        
        for n,m in enumerate(new_metas):
            # m[key], m[value], m[mode]
            key = m['key']
            value = m['value']
            mode = m['mode']

            
            if not key in self.metadatas.keys():  
                # if the post doest have such a metadatas...
                if mode in ('add', 'set'):
                    # we can directly set it to the wanted value
                    self.metadatas.update({key: value})
                    print('  ├ ⚠️"{}" isn\'t a property yet. Creating it.'.format(key))
                    datas_before.update({key: "/"} ) # we remember that we created the new property
                else:
                    # we want to remove the value of a key that doesn't exist anyway
                    # we skip
                    print('  └ No metadatas [{}] in "{}"... Skipped'.format(key, self.filepath.stem) )
                    return(0)
            else:
                if key not in datas_before:
                    # we save metadatass as they were BEFORE editing
                    datas_before.update({key: str(self.metadatas[key])} )
                    
            try:
                
                match mode:
                    case 'set':
                        # mode where we erase and set a property to a new value
                        if isinstance(self.metadatas[key], str):
                            self.metadatas[key] = value
                        elif  isinstance(self.metadatas[key], list):
                            self.metadatas[key] = list(value)
                        else:
                            print('  ├ Unsupported metadatas structure : "{}" [{}]'.format(
                                key, type(self.metadatas[key]) ) )

                    case 'add':
                        # mode where we add value to a property. 
                        if isinstance(self.metadatas[key], str):
                            if self.metadatas[key] == "":
                                self.metadata = str(value)
                            elif self.metadatas[key] == value:
                                pass
                            else:
                                self.metadatas[key] += " {}".format(value)
                        elif  isinstance(self.metadatas[key], list):
                            if 'None' in self.metadatas[key]:
                                self.metadatas[key] = list()
                                self.metadatas[key].append(value)
                            elif value not in self.metadatas[key]:
                                self.metadatas[key].append(value)
                        else:
                            print('  ├ Unsupported metadatas structure : "{}" [{}]'.format(
                                key, type(self.metadatas[key]) ) )

                    case 'remove':
                        # mode where we remove a value from a property.
                        if isinstance(self.metadatas[key], list):
                            if value in self.metadatas[key]:
                                self.metadatas[key].remove( value )
                        else:
                            print('  ├ Unsupported metadatas structure : "{}" [{}]'.format(
                                key, type(self.metadatas[key]) ) )
            except KeyError:
                print('     └ Metadatas "{}" doesn\'t exist'.format(self.metadatas[key]) )
            
            # we save the new metadatas for comparison
            datas_after.update({key: str(self.metadatas[key])})
        
        
        # Let's recap changes for the user's approval
        for k, i in enumerate(datas_before.keys()):
            
            # If it's the last line, we close the border character. Purely esthetic effect.
            if k == len(datas_before.keys())-1 and n == len(new_metas)-1: 
                bar='└'
            else:
                bar="│" 
                
            print("  ├ {}".format(i)) # print the metadata being edited
            print("  │ ├ Before: {}".format(datas_before[i])) # metadatas before edition    
            print("  {} └ Now:    {}".format(bar, datas_after[i]) ) #metadatas after edition
        
        return(True)
        
        
        
    def reload(self):
        """reload Object to match the file"""
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
        print('💾', 'Saving {} …'.format(self.filepath.name))
        with open( self.filepath, 'w' ) as file:
            file.write( self.get(displayFull=True) )
            
    def delete(self):
        pathlib.Path( fullpath( self.filepath) ).unlink()
            
    
    def print(self, displayFull=False):
        print( self.get(displayFull) )
    
    def describe(self):
        """Debut tool to help me with metadatas variable types"""
        for i in self.metadatas:
            print(i, type(self.metadatas[i]) )


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
                    regex= r"(\w+):([\w-]+)" 
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
                    print(self.list[-1])


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
                    
                        if i[0] == 'file':
                            if not normalize(i[1]) in normalize(j.filepath.name):
                                echo('remove file', normalize(i[1]), normalize(j.filepath.name))
                                if k not in removelist:
                                    removelist.append( k )
                            
                        elif i[0] == 'content':
                            if not " {} ".format(normalize(i[1])) in normalize(j.content):
                                echo('remove content from', j.filepath)
                                if k not in removelist:
                                    removelist.append( k )
                        
                        elif i[0] in j.metadatas:
                            if not normalize(i[1]) in normalize(j.metadatas[i[0]]):
                                echo('remove with tag {}!={} from {}'.format(normalize(i[1]), normalize(j.metadatas[i[0]]), j.filepath.name))
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
