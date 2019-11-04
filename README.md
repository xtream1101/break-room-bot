# Connect 4 slack bot


## Server
Run server for slacks webhook `gunicorn server:api -w 2 --reload`

### ENV vars to set
- `REDIS_HOST`
- `REDIS_PASSWORD`
- `RENDERED_IMAGES`
- `BASE_URL`s


### Slack bot settings

#### Slash Command
Set the Request Url to be `https://YOUR_DOMAIN/slack/connect4`.  
Enable the checkbox for _Escape channels, users, and links sent to your app_  


#### Interactive Components
Enable and add the Request Url to be `https://YOUR_DOMAIN/slack/connect4/button`


## Tests
Run tests `pytest -v`  
