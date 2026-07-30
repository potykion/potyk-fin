# potyk-fin

> spending tracking and savings
> ex https://docs.google.com/spreadsheets/d/1-gP3FTcAp4yAFnzMWaLnpEPn7C054V8KdYHYCBFOJwU/edit?usp=sharing

## Links

- [Github](https://github.com/potykion/potyk-fin.git)

## Prod Setup

### First

```shell
ssh-keygen
# example pub
# paste it to https://github.com/settings/keys
cat .ssh/id_ed25519.pub

ssh -l leybovich-nikita 84.201.131.244
# e.g. git@github.com:potykion/potyk-fin.git
git clone git@github.com:potykion/potyk-fin.git

cd potyk-fin
python3 -m venv ".venv"
source ./.venv/bin/activate
pip install -r requirements.txt
# fill env w FLASK_APP=main & FLASK_SECRET=...
nano .env

sudo cp ./potyk-fin.service /etc/systemd/system/potyk-fin.service
sudo chmod 644 /etc/systemd/system/potyk-fin.service
sudo systemctl enable --now potyk-fin.service

```

### Update

```shell
ssh -l leybovich-nikita 84.201.131.244
cd potyk-fin
git pull

source ./.venv/bin/activate
pip install -r requirements.txt 

sudo systemctl restart potyk-fin.service
```
