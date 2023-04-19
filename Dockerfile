# first layer is our python base image enabling us to run pip
FROM python:3.10-windowsservercore-ltsc2022

# create directory in the container for adding your files
WORKDIR /user/src/app

# copy over the requirements file and run pip install to install the packages into your container at the directory defined above
COPY ./mt5_leader/requirements.txt ./
RUN python.exe -m pip install --upgrade pip
RUN pip install --no-cache-dir --upgrade -r requirements.txt
COPY ./mt5_leader/ ./mt5_leader/
COPY ["/MetaTrader 5/", "/MetaTrader 5/"]
# enter entry point parameters executing the container
ENTRYPOINT ["powershell.exe"]

# exposing the port to match the port in the runserver.py file
CMD ["python", "mt5_leader/leader.py"]

# build
# docker build -t mt5_leader .
# run
# docker run --name mt5-leader <image_id>