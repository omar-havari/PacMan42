Build the image with

docker build -t <name_of_container> .

Then run these 2 commands:
xhost +local:docker
docker run -e DISPLAY=$DISPLAY -e LIBGL_ALWAYS_SOFTWARE=1 -v /tmp/.X11-unix:/tmp/.X11-unix pacman

To pull from DockerHub you run:
docker pull "username_of_repo_owner"/"name_of_container"
