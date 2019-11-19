# Connect 4 slack bot

## Adding Connect4 to your team
[![Add to Slack](https://platform.slack-edge.com/img/add_to_slack.png)](https://slack.com/oauth/authorize?scope=commands,chat:write:bot&client_id=5199961139.818403121988)


# Running on your own server

## Server
Run server for slacks webhook `gunicorn server:api -w 2 --reload`

### ENV vars to set
- `REDIS_HOST`
- `REDIS_PASSWORD`
- `BASE_URL`
- `RENDERED_IMAGES_BUCKET` - Needs to be public
- `GAME_HISTORY_BUCKET` - Needs to be public
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
Set the Request Url to be `https://YOUR_DOMAIN/slack/connect4`.  
Enable the checkbox for _Escape channels, users, and links sent to your app_  


#### Interactive Components
Enable and add the Request Url to be `https://YOUR_DOMAIN/slack/connect4/button`


### Assets

In the folder `src/assets`, create a theme folder, i.e. `src/assets/classic` Inside that folder you will need to put the following assets for your theme. All assets must be png format to allow for transparency.  
If you add a file called `about.txt` into your theme folder, then that text will render next to your theme when a user uses the command `/connect4 themes`. Only the first 200 characters will be displayed.  

The theme files that created the assets can be stored in the directory `raw_assets/`.  

#### Board
_Required_  
Filename: `board.png`  
Width: `438px`  
Height: `377px` (actual board size), can be taller if some type of header is wanted, but the board must start in the bottom left.  
From the bottom left, the pieces are 11px to the right and 11px from the bottom. This repeats until you get a 7 wide and 6 heigh board (creating the above dimensions).

#### Pieces
_Required_  
Filenames: `player1.png` & `player2.png`  
Width: `50px`  
Height: `50px`  
These are the player pieces and will be rendered on the board in the correct spots as players play. When rendered, they are layered on top of the `board.png`

#### Latest Move
_Optional_  
Filename: `latest_move.png`  
Width: any  
Height: any  
This will denote where the last player was played. It will be rendered above the `player*.png` & `board.png`. It will render center to the players piece which is why size does not matter.

#### Won spots
_Optional_  
Filename: `won.png`  
Width: any  
Height: any  
When a game has been won by a player, this will overlay the pieces that let them win. In this case, the `latest_move.png` will NOT render. It will render center to the players piece which is why size does not matter.  

## Tests
Run tests `pytest -v`  
