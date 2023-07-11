FROM tobix/pywine:3.11

ADD ./mt5_leader ./mt5_leader
ADD ./MT5 ./MT5

RUN cd / && apt update && apt install -y xvfb && \
    wine python -m pip install --upgrade pip setuptools && \
    wine python -m pip install -r ./mt5_leader/requirements.txt

CMD xvfb-run wine python -u ./mt5_leader/leader.py

# build
# docker build -t mt5-leader .
#
# run
# docker run -e EXCHANGE_ID=<exchange_pk> --name mt5-leader <image_id>
