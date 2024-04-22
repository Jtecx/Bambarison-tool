# Bambarison tool!
Builds images for comparison purposes by stacking them side by side. Console only, designed for Lewdiverse from MXDX

Requirements:
Pillow, numpy, queue, threading, logging.

Tested on Python 3.11

Usage:
Download the repo, and create a folder called "Originals". It is highly recommended you use an IDE such as Pycharm or Intellij Idea's community edition. You will also need to install python 3.11 or greater, and setting up a venv for the project is highly recommended. 
If you don't know what that means, google "Pycharm/Intellij Python Venv"
Inside "Originals", drop the character sheet pngs.
Leave the file name for the character sheets as what MXDX had given you, as it's used for the parsing of the character. In case you renamed it, the expected format is "000CharName.png"

Afterwards, just start the script!

It will ask you for the number of images you want to compare, which will dictate how long the resulting image will be,
Then it will ask you the character number you would like to compare. This is the digits in your filename, and should be identical to the value shown in the image itself, in the top left corner.
Finally, it will ask if you are comparing the clothed or nude version.
It will loop for as many times as you set initially.

After this, it will process and return the completed file. Do note however, the filename consists of only the character number, their state of clothing, and not their name as files have a limit to how long they can be.

Potential issues:
File name may be too long, this can be remedied by simply force setting the output name instead in the script. This is an OS issue, limiting total characters of up to 255 characters.
