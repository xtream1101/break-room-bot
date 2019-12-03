# Break Room Bot
Take a break and play some games inside of slack  


## Adding Break Bot to your
### Slack
[![Add to Slack](https://platform.slack-edge.com/img/add_to_slack.png)](https://slack.com/oauth/authorize?client_id=5199961139.860911396486&scope=commands,chat:write:bot)




# Running on your own server


## Services needs
 - S3 buckets, either through aws or running your own using MinIO or the like.
 - Redis cache
 - API server where this app will run

## ENV vars to set
- `REDIS_HOST`
- `REDIS_PASSWORD`
- `BASE_URL`
- `RENDERED_IMAGES_BUCKET` - Needs to be public
- `GAME_HISTORY_BUCKET` - Needs to be private, TODO: change to save to postgres
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `S3_ENDPOINT` - optional, will default to aws s3
- `OAUTH_BUCKET` - only needed if oauth is being used. Needs to be private
- `SLACKBOT_CLIENT_SECRET` - only needed if oauth is being used
- `SLACKBOT_CLIENT_ID` - only needed if oauth is being used


### Slack bot settings

#### Permissions
Needs:
- `chat:write:bot`
- `commands`

#### Slash Command
- `/breakroom`  
    Set the Request url to be `https://YOUR_DOMAIN/slack/breakroom`.  
 
- `/connect4`  
    Set the Request url to be `https://YOUR_DOMAIN/slack/connect4`.  
    Enable the checkbox for _Escape channels, users, and links sent to your app_  


#### Interactive Components
Enable and add the Request Url to be `https://YOUR_DOMAIN/slack/interactive`  

#### For slack oauth
Set up a redirect url: `https://YOUR_DOMAIN/slack/oauth`

## Running the server
Run the api server: `gunicorn server:api -w 2 --reload`
