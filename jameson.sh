#! /bin/bash
##==========================================
## Jameson, the friendly helper for Hugo (gohugo.io)
## (named after J. Jonah Jameson)
##
##  written by jabossu under GPL3

version="1.6.5"
echo "
____________________________________________________________________________________
   oooo                                                                      
   \`888                                                                      
    888  .oooo.   ooo. .oo.  .oo.    .ooooo.   .oooo.o  .ooooo.  ooo. .oo.   
    888 \`P  )88b  \`888P\"Y88bP\"Y88b  d88' \`88b d88(  \"8 d88' \`88b \`888P\"Y88b  
    888  .oP\"888   888   888   888  888ooo888 \`\"Y88b.  888   888  888   888  
    888 d8(  888   888   888   888  888    .o o.  )88b 888   888  888   888  
.o. 88P \`Y888\"\"8o o888o o888o o888o \`Y8bod8P' 8\"\"888P' \`Y8bod8P' o888o o888o 
\`Y888P                                                                       v$version
____________________________________________________________________________________
"

curdir=`pwd`

function edit { 
	$editor $1 2>/dev/null 
	return 0
}

##==========================================
## Configuration steps
##==========================================

# Reading config file
configFile="$HOME/.config/jameson.conf"
if [[ ! -f $configFile ]];
then
    echo " * Error : config file doesn't exist."
    echo " ! creating a file with default options"
        mkdir "$HOME/.config"
        echo "## Jameson Config File :
root=$HOME/myHugoProject
editor=nano
mainbranch=main
workingbranch=writting" > $configFile
fi

# Setting editor. Nano is the default
editor="$(grep editor $configFile | cut -d = -f 2)" 
if [[ ! -x "$(command -v $editor)" ]];
then
    echo " * Error :Editor $editor not found"
    echo " * Edit $configFile and choose a working editing software"
    exit 1
fi

# Setting root directory and checking if it exists
root="$(grep root $configFile | cut -d = -f 2)"
if [[ ! -d $root ]];
then
    echo " * Root directory set incorrectly in config file. Cannot run."
    exit 1
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
    
##==========================================    
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
    
##==========================================
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

##==========================================
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
 
 ##==========================================   
# Import a picture into the project picture folder
	# option : -k to keep source file
    import)
        cd "$curdir" #we need to stay where the command was run from
        
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
            exiftool -all= "$inputFile.webp"
            oldsize=$(ls -lh "$2" | awk '{print  $5}')
            newsize=$(ls -lh "$inputFile".webp | awk '{print  $5}')
            echo "    ↳ file size : old=$oldsize ; new=$newsize"
        else
            # Create a copy to work safely
            cp "$2" "$inputFile.webp"
        fi
        # create thumbnail
        convert "$2" -resize 400x600 "$inputFile-thumb.webp"
        exiftool -all= "$inputFile-thumb.webp"
        
        # Check if the output should have another filename
        if [[ -v 3 ]];
        then
            outputFile="$3"
        else
            # Remove personnal data from filename
            outputFile="$(echo $inputFile | sed 's/jabosu/mijourney/')"
        fi
        
        # Remove special characters
        outputFile="$(echo $outputFile | sed -r 's/([0-9. -@!*$=&]+)-/_/g' )"
        
        #limit longer filenames
        outputFile="$(echo $outputFile | cut -c -62)"
        
        echo " * Copying files to project folder..."
            yearmonth="$(date -u +%Y-%m)"
            outputDirectory="$root/static/img/pictures/$yearmonth"
            mkdir -p $outputDirectory
            
            ## Check if destination already exists to avoid removing it
            if [[ -f $outputDirectory/$outputFile.webp ]] ; then
                echo " ! ERROR : file already exists."
                echo " ! $outputDirectory/$outputFile.webp found"
                echo " ! use a destination parameter to still import the image"
                exit 1
            else
                mv "$inputFile.webp" "$outputDirectory/$outputFile.webp"
                mv "$inputFile-thumb.webp" "$outputDirectory/$outputFile-thumb.webp"
            fi
            
            cd "$root"
            echo " * Committing changes..."
            git add "$outputDirectory/$outputFile.webp" "$outputDirectory/$outputFile-thumb.webp"
            git commit --quiet -m "imported images $outputFile"
            
        echo " * [SUCCESS] Images imported."
        echo -n "/img/pictures/$yearmonth/$outputFile.webp" | xclip -sel clip 2>/dev/null && echo " * image location copied to clipboard" || echo " ! could not copy file path. Maybe install xclip ?"
    ;;
        
##==========================================
# Edits a post
    edit)
        echo " - Editing posts with keyword \"$2\"..."
        
        results=$(fd "$2" content/ -t f)
        if [[ $results == "" ]] ; then
            echo " - no matching file found ! "
            exit 1
        fi

        echo " - Found matching content:"
        echo "   ======================="       
        n=0; for i in $results  # Get all textfiles relevant and work on each of them in order
        do
            let "n+=1"
            echo  -e "\t$n. $i"
        done
        echo ''
        
        if [[ "$n" -eq 1 ]]; then
            echo " - only one result. Editing..."
        else
            read -p " > which file to edit ? [1-$n ; n=exit] " edit
        
            re='^[0-9]+$'
            if [[ $edit =~ $re ]] ; then
            
                if [[ "$edit" -le $n ]] ; then
                    j=0
                    for i in $results
                    do
                        let "j+=1"
                        if [ "$j" -eq "$edit" ]; then
                            echo " ! Opening $i for editing"
                            edit "$i" 
                            git add -A
                            git commit --quiet
                            exit 0
                        fi
                    done
                fi
            fi
        fi

        drafted=`grep 'draft: true' "$i"`
        if [ "$drafted" != '' ]; then
        # if the post is a draft : we have to update the date to today
            echo ' * Post is drafted : updating post date'
            sed "s/date: .*/date: $(date +%Y-%m-%d)/" "$i" > tmp
            mv tmp "$i" ## we have to do this or 'sed' removes all the content
        else
        # if the post is already published, we update lastmod date
            echo ' * Post is already published : updating lastmod'
            if [[ "$(grep lastmod $i)" ]];then
                sed "s/lastmod: .*/lastmod: $(date +%Y-%m-%d)/" "$i" > tmp
            else
                sed "s/^date:/lastmod: $(date +%Y-%m-%d)\ndate:/" "$i" > tmp
            fi
            mv tmp "$i" ## we have to do this or 'sed' removes all the content
        fi
        
        echo " * Opening editor on '$i'"
        
        if [ "$3" == '-w' ]; then
        # if option -w if passed...
        #open file for edit while the local webserver is running so we can look at it
            if [ ! "$(pidof hugo &>/dev/null)" ]; then
                # if hugo server is not yet running
                hugo server -D --disableFastRender &>/dev/null &
                echo " ! Starting local webserver…"
                sleep 1s # slight delay for web server to start properly
            fi
            
            echo " ! Webserver running at http://localhost:1313/ ; opening web browser"
            tmp=${i/content\///} ; address=${tmp/\.md//}
            xdg-open "http://localhost:1313/$address" &>/dev/null # open web browser at the same time
        fi
        
        edit "$i" 2>/dev/null # open editor on file
        ### ... work gets done ...
        pkill hugo # editing is done : kill local browser
        
        if [ $n -eq '0' ] ; then
            echo " ! error : no post found"
            echo ""
            exit 1
        fi
        
        echo " * Committing changes..."
        echo -n ' - ' && git add -A && git commit --quiet 
    ;;
    
##==========================================
# Create a new post and open it in the text editor
    new)
        echo " * Creating a new post..."
        post="$(echo $2 | sed 's/ /-/g')"
        if [[ "$post" =~ "/" ]];
        then
            kind=$(echo "$post" | awk -F/ '{print $1}')
            if [[ -f "archetypes/$kind.md" ]];
            then
                echo " * [SUCCESS] Created new post as $kind"
                hugo new "posts/$post.md" --kind "$kind"
                edit "content/posts/$post.md" 
            else
                echo " * [ERROR] Archetype '$kind' does not exist. Avaiable archetypes are:"
                ls archetypes
            fi
        else
        
            hugo new "posts/$post.md" &&\
	            echo " * [SUCCESS] post created" &&\
	            edit "content/posts/$post.md" 
            git add "content/posts/$post.md"
            git commit --quiet -m "New post : $post"
        fi
    ;;

##==========================================
# Run hugo local server
    work)
        echo -n " * Starting webserver... "
        pidof hugo 2&>/dev/null && running=true || running=false
        if [ "$running" == true ] ; then
            echo "[ERROR]"
            echo " ! Already running... skipping."
            exit 1
        else
            hugo server -D --disableFastRender  2&>/dev/null &
            # -D : render Drafts
            # - --disable Fast Render so updates to CSS files are displayed too 
            sleep 1s
            echo "[DONE]"
        fi
        echo " * Opening browser..."
        xdg-open http://localhost:1313
    ;;

# Run hugo local server
    stop)
        pidof hugo 2&>/dev/null && running=true || running=false
        if [ "$running" == true ] ; then
            echo -n " * Stopping webserver... "
            pkill hugo && echo '[DONE]'
        else
            echo " * Webserver not running - doing nothing"
        fi
    ;;

##==========================================
# List & edit drafts
    drafts)
        echo -e "The following posts are still drafted :\n"
        j=0
        for i in $(grep "draft: true" content/  -r | \
            sed -z 's/content\/posts\///g' | \
            cut -d ':' -f 1 | \
            sed -z 's/.md//g')
        do
            let "j+=1"
            echo -e "\t$j. $i"
        done
        
        echo ""
        read -p " > Edit a drafts ? [1-$j ; n=exit] " edit
        
        re='^[0-9]+$'
        if [[ $edit =~ $re ]] ; then
        
            if [ "$edit" -le $j ] ; then
                j=0
                for i in $(grep "draft: true" content/  -r | \
                    sed -z 's/content\/posts\///g' | \
                    cut -d ':' -f 1 | \
                    sed -z 's/.md//g')
                do
                    let "j+=1"
                    if [ "$j" -eq "$edit" ]; then
                        echo " ! Opening $i for editing"
                        edit "content/posts/$i.md" 
                        git add -A
                        git commit --quiet
                        exit 0
                    fi
                done
            fi
            echo " * No draft selected"
        fi
    ;;
    
    open)
        # Open project folder
        
        # open a post older
        if [[ "$2" =~ "posts" ]] ; then
            if [[ -d "$root/content/$2" ]] ; then
                echo " - Opening posts $2"
                xdg-open "$root/content/$2"
            else
                echo " ! Folder doesn't exist"
                echo " - avaiable options :"
                ls -1d $root/content/posts/*/ | rev | cut -d '/' -f 2-3 | rev
            fi
        #open any folder
        elif [[ -d "$root/$2" ]] ; then
            echo " - Opening $root/$2"
            xdg-open "$root/$2"
        # open root folder
        else
            echo " - Opening $root"
            xdg-open $root
        fi
    ;;

##==========================================   
# List all posts, filter by keyword
    list)
        keyword="$3"
        command="ls -F --group-directories-first -v"

        echo "Written Posts:"
        echo "--------------"
        if [[ -n $2 ]];
        then
            # filter by keyword
            $command content/posts/$2 
        else
            # no keyword to filter
            $command content/posts/ 
        fi
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
         - list <keyword>       : list posts. Filter by keyword (optionnal)
         
        Writting and content management tools
         - import <imagefile>   : convert image to WEBP and import it to the image folder
         - save                 : save changes 
         - sync                 : pull and push branches to sync to origin
         - publish              : publish changes to main git branch
         - save publish         : save changes, then merges branch to main branch
         "
    ;;
    
# Help with shortcodes
    shortcode)
        if [ -f "layouts/shortcodes/$2.html" ] ; then
            echo " - Shortcode $2 :"
            grep shortdescr "layouts/shortcodes/$2.html"
            grep shortsyntax "layouts/shortcodes/$2.html"
        else
            echo " - Avaiable shortcodes :"
            echo "   ====================="
            ls layouts/shortcodes/
        fi
    ;;
    
# No valid argument
    *)
        echo "Unknown argument. Use \"jameson help\""
    ;;
esac

echo " ---bye---"
cd "$curdir"
