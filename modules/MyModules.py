import yaml, subprocess, shlex, pathlib, datetime, pyperclip, re
import cfg
import modules.gitwrapper as gitwrapper
from unidecode import unidecode

def fullpath(f):
    """prepend cfg.v['root'] and return full string"""
    r = "{}/{}".format(cfg.v['root'], f).replace('//', '/')
    return( r )

def normalize(s):
    """Takes a string, lower all letters, remove diacritics and return a normalized string"""
    r = unidecode(str(s).casefold()) 
    regex = r"[^\w.-]+" 
    r = re.sub( regex, "_", r )
    return(r)
    

def print_line(char="—", lenght=70):
    """Print a line of lenght with char"""
    line=""
    for i in range(0, lenght):
        line += char
    print(line)

def echo( *text ):
    """Outputs text, only if verbose mode is active"""
    if cfg.verbose_mode:
        print( "ℹ️", str(text) )
    
def edit( filename ):
    """Open given file with user chosen editor"""
    command = shlex.split( cfg.v['editor'] )
    command.append( filename )
    
    print("✏️ ", 'Opening "{}"'.format( filename ))
    try:
        subprocess.run( 
            command, cwd=cfg.v['root'], 
            stderr=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL)
        gitwrapper.commit('Edited "{}"'.format(filename))
    except KeyboardInterrupt:
        print(" Quit")
        exit(1)

def convert_image( image_path, thumb=True ):
    """Take an image and convert it to WEBP. Resize it if thum is true"""
    
    resize=""
    newname = image_path.stem # we remove the sufix
    newname = newname.replace( 'jabosu', 'midjourney' ) #we anatomize the filename
    newname = normalize(newname) # remove unusual character from filename
    if thumb == True:
        resize = "-resize 400x600"
        newname += "-thumb"
        print("⬇️ ", "Creating thumbnail...")
    else:
        print("🔁", "Converting image to webp...")
    
    target_directory = '{}static/img/pictures/{}'.format(cfg.v['root'], datetime.date.today().strftime('%Y/%m'))
    pathlib.Path( target_directory ).mkdir( parents=True, exist_ok=True )
    new_image_path = pathlib.Path( "{}/{}.webp".format(target_directory, newname) )
    
    if new_image_path.exists():
        print("⛔", 'Error : file "{}" already exists in {}/'.format( new_image_path.name, target_directory ))
        exit(1)
    
    command = 'magick "{}" {} "{}"'.format(
            image_path.absolute(),
            resize,
            new_image_path.absolute() 
        )
    
    r = subprocess.run( shlex.split(command), stderr=subprocess.PIPE, text=True )

    if "improper image header" in r.stderr :
        print("⛔", "File provided in argument is not an image")
        exit(1)
    elif r.stderr != "":
        print("⛔", "[ERROR]", r.stderr.rstrip())
        print(r.args)
        exit(1)
        
        # let's remove all metadatas from imported image
        command = 'exiftool -overwrite_original -all= "{}"'.format( new_image_path.absolute())
        subprocess.run( shlex.split(command), stdout=subprocess.DEVNULL, stderr=subprocess.PIPE )
    
    return( new_image_path.relative_to( "{}/static".format(cfg.v['root']) ) )


def import_image( filepath, keep_sourcefile=False ):
    """Try to convert image to webp and move it the the right directory"""
    image_path = pathlib.Path( filepath )
    
    if not image_path.is_file():
        print("⛔","File not found")
        exit(1)
    
    # convert_image() will both optimize the image and move it to the right folder
    # so we call it even if source file is already WEBP  
    new_image = convert_image(image_path, thumb=False )
    # Create thumbnail
    convert_image(image_path,thumb=True)
        
    if not keep_sourcefile:
        print("🚮", "Removing original image. (pass --keep to keep)")
        image_path.unlink()
        
    # for convenience, copy the new filepath to user's clipboard
    new_filepath = "/{}".format(new_image) 
    pyperclip.copy(new_filepath)
    print("✅", 'Success ! filepath copied to clipboard : "{}"'.format(new_filepath))
