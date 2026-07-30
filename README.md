# HOW TO USE TEMPLATE

- Replace following vars & commands with ur values:

| Var                | Description                 | Sample value                                 |
|--------------------|-----------------------------|----------------------------------------------|
| `$PROJECT`         | Project name                |                                              |
| `$PROJ_DESC`       | Project description         |                                              |
| `$HOME`            | Home dir                    | `/home/leybovich-nikita`                     |
| `$PORT`            | Port where service will run | `5003`                                       |
| `ssh -l $USER $IP` | Ssh creds                   | `ssh -l leybovich-nikita 84.201.131.244`     |
| `$REPO_URL_SSH`    | Ssh git repo url            | `git@github.com:potykion/potyk-stats.git`    |
| `$REPO_URL`        | Http git repo url           | `https://github.com/potykion/potyk-mu-2.git` |

- Rename following files & occurrences to ur names:
    - `example.service` - systemctl service &
- Create `.env` from `.evn.example` vars
- Create `.venv` & install reqs: `pip install -r requirements-dev.txt`

# $PROJECT

> $PROJ_DESC

## Links

- [Github]($REPO_URL)

## Prod Setup

### First

```shell
ssh-keygen
# example pub
# paste it to https://github.com/settings/keys
cat .ssh/id_ed25519.pub

ssh -l $USER $IP
# e.g. git@github.com:potykion/wine-wish.git
git clone $REPO_URL_SSH

cd $PROJECT
python3 -m venv ".venv"
source ./.venv/bin/activate
pip install -r requirements.txt
# fill env w FLASK_APP=main & FLASK_SECRET=...
nano .env

sudo cp ./example.service /etc/systemd/system/example.service
sudo chmod 644 /etc/systemd/system/example.service
sudo systemctl enable --now example.service

```

### Update

```shell
ssh -l $USER $IP
cd $PROJECT
git pull
sudo systemctl restart example.service
```
