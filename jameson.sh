#! /bin/bash

echo "
   oooo                                                                      
   \`888                                                                      
    888  .oooo.   ooo. .oo.  .oo.    .ooooo.   .oooo.o  .ooooo.  ooo. .oo.   
    888 \`P  )88b  \`888P\"Y88bP\"Y88b  d88' \`88b d88(  \"8 d88' \`88b \`888P\"Y88b  
    888  .oP\"888   888   888   888  888ooo888 \`\"Y88b.  888   888  888   888  
    888 d8(  888   888   888   888  888    .o o.  )88b 888   888  888   888  
.o. 88P \`Y888\"\"8o o888o o888o o888o \`Y8bod8P' 8\"\"888P' \`Y8bod8P' o888o o888o 
\`Y888P                                                                       v$version
"

version="1.0"
curdir=`pwd`

# Reading config file
configFile="$HOME/.config/jameson.conf"
[[ -f $configFile ]] || echo " * Error : config file doesn't exist." || exit 1

# Setting editor. Nano is the default
editor="$(grep editor $configFile | cut -d = -f 2)" 
[[ -x $editor ]] || echo " * Editor not set in config file. Using Nano" || editor='nano'

root="$(grep root $configFile | cut -d = -f 2)"
[[ -d $root ]] || echo " * Root directory set incorrectly in config file. Cannot run." || exit 3



cd "$root"

case $1 in
    
    #Save the curent branch and push it
    save)
        # hugo -D
        git pull
	    git add .
	    git commit
	    git push
	    if [[ $2 == "publish" ]];
	    then
	        jameson publish
        fi
    ;;

    # Merge with the main branch and push changes. Updates the website
    publish)
        git checkout main
        git merge writting
        git push
        git checkout writting
        echo "Changes published"
    ;;
    
    #Import a picture to the picture folder
    import)
        cd $curdir #we need to stay where the command was run from
        
        ## If no argument was given, fail safely
        if [[ ! -v 2 ]];
        then
            echo "syntax for import: jameson import <sourcepath> [<newname>]"
            exit
        fi
        
        # Get input file name and extension
        inputFile=$(basename -- "$2")
        inputFileFormat="${inputFile##*.}"
        inputFile="${inputFile%.*}"
        
        # If not a WEBP image, do the conversion
        if [[ $inputFileFormat != "webp" ]];
        then
            echo " * Convert image to WEBP"
            convert "$2" "$inputFile.webp"
            oldsize=$(ls -lh "$2" | awk '{print  $5}')
            newsize=$(ls -lh "$inputFile".webp | awk '{print  $5}')
            echo " * file size : old=$oldsize ; new=$newsize"
        else
            # Create a copy to work safely
            cp "$2" "$inputFile.webp"
        fi
        # give back an extension so we can work more easily
        inputFile="$inputFile.webp"
        
        # Check if the output should have another filename
        if [[ -v 3 ]];
        then
            outputFile="$3"
        else
            outputFile="$inputFile"
        fi
        outputFile="$(echo $outputFile | sed -r 's/([0-9. -]+)-/ -/g' )"
        
        echo -n " * "
        cp -v "$inputFile" "$root/static/img/pictures/$outputFile"
        echo "/img/pictures/$outputFile" | xclip -sel clip && echo " * image location copied to clipboard"
        
        rm "$inputFile" "$2" # discard the original and copy we made
    ;;
        
    # Edits a post
    edit)
        echo " * Opening editor..."
        fd $2 content/ -x $editor {}
    ;;
        
    new)
        if [[ "$2" =~ "/" ]];
        then
            kind=$(echo "$2" | awk -F/ '{print $1}')
            hugo new posts/$2.md --kind $kind
        else
            hugo new posts/$2.md
        fi
        $editor content/posts/$2.md
    ;;
    
    work)
        hugo server -D
    ;;
    
esac

cd $curdir
