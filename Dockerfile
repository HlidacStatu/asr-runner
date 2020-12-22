FROM python:3.9.1-buster

run apt-get update
run apt-get install -y apt-transport-https ca-certificates curl gnupg-agent software-properties-common
run curl -fsSL https://download.docker.com/linux/debian/gpg | apt-key add -
run add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/debian $(lsb_release -cs) stable"
run apt-get update
run apt-get install -y docker-ce-cli

WORKDIR /usr/src/app
COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "./main.py" ]
