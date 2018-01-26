# FullPless VK Bot

This bot provides an ability to publish/update community posts conditionally

## Features

* Delay wall post publish (up to 100 hours)
* Update wall post on required likes count
* Publish protected community videos

## Usage

At first we need to build Docker image for FullPless bot

```
docker build -t fullpless-bot:1.0.0 .
```

Also we need to start Selenium standalone node

```
docker run -d --name selenium -p 172.17.0.1:4444:4444 -p 127.0.0.1:5900:5900 -v /dev/shm:/dev/shm selenium/standalone-chrome-debug:latest
```

Now we could start FullPless bot

```
docker run -d --name fullpless-bot -e VK_USER="<VK login>" -e VK_PASSWORD="<VK password>" -e COMMUNITY_ID="<VK community ID>" -e ADMIN_LIST=<comma delimited list of admins VK ID> fullpless-bot:1.0.0
```