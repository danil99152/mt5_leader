FROM tobix/pywine:3.10

ADD ./mt5_leader ./mt5_leader
ADD ./MetaTrader5 ./MetaTrader5

RUN cd / && apt update && apt install -y xvfb && \
    wine python -m pip install --upgrade pip setuptools && \
    wine python -m pip install -r ./mt5_leader/requirements.txt

CMD xvfb-run wine python -u ./mt5_leader/leader.py

# build
# docker build -t mt5-leader .
#
# run
# docker run --name mt5-leader <image_id> --env ACCOUNT_ID=<account_pk>
