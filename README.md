# Jameson
the humble editing-helper for [Hugo](http://gohugo.io) static website generator.

> Flowers? How much? If you spend any more on this thing, you can pick the daisies off my grave! Get plastic!
> <cite>— J. Jonah Jameson, Spider-Man 2</cite>

## The Goal

Jameson helps me manage my git branches and commits to write my blog created with hugo.
It's a collection of shortcuts bundled in a simple command, that will run from your project directory.
It's nothing much, just a simple bash script. Still, it gets out of the way and allows you to focus on writing posts instead of reading the git manpages every few minutes.

## How to use
1. Place the shell script into your $PATH
2. Make it executable : `$ chmod +x jameson.sh`
3. Enjoy

You can access the help using `$ jameson.sh help`

To update : simply replace the old version with a new.

## Features
- configure project directory so all commands run from there
- save files, create commits and push branches in a single command
- create new posts and uses hugo archetypes
- manage Drafts
- convert images to webp and import them into your project for better size optimization
- configurable through a config file

## Configuration
Jameson now requires a configfile to get it's main parameters, most notably the editor to invoke and where your hugo project is.

An example is provided in this git repo, and Jameson with create and populate a dummy config file if none is found.

The config file should be placed in `$HOME/.config/jameson/jameson.conf`

### root
```root=/home/username/myhugoblogroot```
the path to the root folder of your hugo project

### editor
```editor=nano```
the command to execute as an editor

### Git branches
```mainbranch=main
workingbranch=writting```
- **Mainbranch** is the production branch : where to push to when you're done with your editing
- **Workingbranch** is where you will edit and create and modify your blog in the time between release.
