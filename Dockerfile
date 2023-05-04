FROM msjpq/wine-vnc:bionic

ADD . .

CMD sleep 1d


# build
# docker build -t myimage .

# run
# docker run -p 8080:8080 -p 5900:5900 --name leader <container_id>