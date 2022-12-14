#! /bin/bash
##==========================================
## Jameson, the friendly helper for Hugo
## (named after J. Jonah Jameson)
##
##  written by jabossu under GPL3

version="1.2"
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

curdir=`pwd`

##==========================================
## Configuration steps
##==========================================

# Reading config file
configFile="$HOME/.config/jameson.conf"
if [[ ! -f $configFile ]];
then
    echo " * Error : config file doesn't exist."
    exit 1
fi

# Setting editor. Nano is the default
editor="$(grep editor $configFile | cut -d = -f 2)" 
if [[ ! -x "$(command -v $editor)" ]];
then
    echo " * Editor $editor not set in config file. Using Nano"
    editor='nano'
fi

# Setting root directory and checking if it exists
root="$(grep root $configFile | cut -d = -f 2)"
if [[ ! -d $root ]];
then
    echo " * Root directory set incorrectly in config file. Cannot run."
    exit 3
fi    

# Setting main branch to publish to
mainbranch="$(grep mainbranch $configFile | cut -d = -f 2)" 
if [[ -z "$mainbranch" ]];
then
    echo " * Production branch unset in config. Using main"
    mainbranch=main
fi

# Setting working branch branch to commit to
workingbranch="$(grep workingbranch $configFile | cut -d = -f 2)" 
if [[ -z "$workingbranch" ]];
then
    echo " * Working branch unset in config. Using main" 
    workingbranch=writting
fi

##==========================================
## Starting for real now
##==========================================
cd "$root" # changing to project directory

## Now reading arguments and acting accordingly
case $1 in
    
    sync)
    ## Syncing all datas to source to prevent conflicts from arising
        echo " * Syncing to source..."
        echo -ne "     - Pulling : "
        git fetch --all
        git pull origin
        echo -ne "     - Pushing : " 
        git push --all origin
        echo ""
    ;;
    
    #Save the current branch and push it
    save)
        #Disable this if you don't need to sync build files:
        # hugo -D 
	    git add .
	    echo -n " * Commiting changes..."
	    git commit
	    echo -e "\n * pushing changes"
	    git push
	    echo -e "\n * [SUCCESS] Changes saved"

	    # if "jameson save publish" was used, publish next
	    [[ $2 == "publish" ]] && jameson publish
    ;;

    # Merge with the main branch and push changes. Updates the website
    publish)
        git checkout $mainbranch
        echo ""
        git merge $workingbranch
        git push
        echo ""
        git checkout $workingbranch
        echo -e "\n * [SUCCESS] Changes published"
    ;;
    
# Import a picture into the project picture folder
	# option : -k to keep source file
    import)
        cd $curdir #we need to stay where the command was run from
        
        ## If no argument was given, fail safely
        if [[ ! -v 2 ]];
        then
            echo " ! [ERROR ] syntax for import: jameson import <sourcepath> [<newname>]"
            exit 1
        elif [[ ! -f "$2" ]]; 
        then
            echo " ! [ERROR] file doesn't exist"
            exit 1        
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
            convert "$2" -resize 300x500 "$inputFile-thumb.webp"
            oldsize=$(ls -lh "$2" | awk '{print  $5}')
            newsize=$(ls -lh "$inputFile".webp | awk '{print  $5}')
            echo "    ??? file size : old=$oldsize ; new=$newsize"
        else
            # Create a copy to work safely
            cp "$2" "$inputFile.webp"
        fi
        # create thumbnail
        convert "$2" -resize 300x500 "$inputFile-thumb.webp"
        
        # Check if the output should have another filename
        if [[ -v 3 ]];
        then
            outputFile="$3"
        else
            outputFile="$inputFile"
        fi
        outputFile="$(echo $outputFile | sed -r 's/([0-9. -]+)-/ -/g' )"
        
        echo " * Copying files to project folder..."
            yearmonth="$(date -u +%Y-%m)"
            outputDirectory="$root/static/img/pictures/$yearmonth"
            mkdir -p $outputDirectory
            cp "$inputFile.webp" "$outputDirectory/$outputFile.webp"
            cp "$inputFile-thumb.webp" "$outputDirectory/$outputFile-thumb.webp"
        echo " * [SUCCESS] Images imported."
        echo -n "/img/pictures/$yearmonth/$outputFile.webp" | xclip -sel clip 2>/dev/null && echo " * image location copied to clipboard" || echo " ! could not copy file path. Maybe install xclip ?"
        
        rm "$inputFile.webp" "$inputFile-thumb.webp" "$2" # discard the original and copy we made
    ;;
        
# Edits a post
    edit)
        echo " * Opening editor..."
        fd "$2" content/ -x $editor {}
    ;;

# Create a new post and open it in the text editor
    new)
        echo " * Creating a new post..."
        if [[ "$2" =~ "/" ]];
        then
            kind=$(echo "$2" | awk -F/ '{print $1}')
            if [[ -f "archetypes/$kind.md" ]];
            then
                echo " * [SUCCESS] Created new post as $kind"
                hugo new "posts/$2.md" --kind "$kind"
                $editor "content/posts/$2.md"
            else
                echo " * [ERROR] Archetype '$kind' does not exist. Avaiable archetypes are:"
                ls archetypes
            fi
        else
            hugo new "posts/$2.md"
            echo " * [SUCCESS] post created"
            $editor "content/posts/$2.md"
        fi
    ;;

# Run hugo local server
    work)
        hugo server -D
    ;;

# List drafts
    drafts)
        echo "The following posts are still drafted :"
        grep "draft: true" content/  -r | sed -z 's/content\// * /g' | cut -d ':' -f 1 
    ;;

# Help
    help)
        echo "syntax: jameson <command> <arguments>
        
        General commands
         - help                 : this help
         
        Manage posts
         - new <title>
           new archetype/title
                                  create a new post title.md
         - work                 : run hugo localhost server
         - edit <title>         : open post in editor
         - drafts               : list drafted posts
         
        Writting and content management tools
         - import <imagefile>   : convert image to WEBP and import it to the image folder
         - save                 : save changes 
         - sync                 : pull and push branches to sync to origin
         - publish              : publish changes to main git branch
         - save publish         : save changes, then merges branch to main branch
         "
    ;;
    
# No valid argument
    *)
        echo "Unknown argument. Use \"jameson help\""
    ;;
esac

echo ""
cd $curdir
