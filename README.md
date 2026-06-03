*This activity has been created as part of the 42 curriculum by kbega, ohavari*

# Setup

## VENVs
2 virtual environments have been created:
pygame_dependencies - **Has dependencies for pygame (has to be activated before running main_menu_UI.py)**
flake8_dependencies - **Has flake8 dependencies for flake8 (part of the lint-check)**

## Code files
Files are yet to be worked through but so far:
main_menu_UI.py - **serving as current entrypoint**
pacman_images.py - **used to draw images to the main menu UI**
.gitignore - **will be used to store secret variables or images used during the making of UI**

## Images
Several images of pacman and the ghosts have been used in a PNG format

# Docker instructions

Build the image with:
docker build -t <name_of_container> .

Then run these 2 commands:
xhost +local:docker
docker run -e DISPLAY=$DISPLAY -e LIBGL_ALWAYS_SOFTWARE=1 -v /tmp/.X11-unix:/tmp/.X11-unix pacman

To pull from DockerHub you run:
docker pull <username_of_repo_owner>/<name_of_container>
