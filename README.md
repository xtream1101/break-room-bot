# Break Room Bot
Take a break and play some games inside of slack  


## Games
- **Connect 4**
- **Mastermind**

Use the slash command `/breakroom` to find out more!  

## Adding BreakRoom Bot to your **Slack Team**

[![Add to Slack](https://platform.slack-edge.com/img/add_to_slack.png)](https://slack.com/oauth/authorize?client_id=5199961139.860911396486&scope=commands,chat:write:bot)


# Creating a custom theme

<details>
  <summary>Connect4</summary>

### Assets

In the folder `src/connect4/assets`, create a theme folder, i.e. `src/connect4/assets/classic` Inside that folder you will need to put the following assets for your theme. All assets must be png format to allow for transparency.  
If you add a file called `about.txt` into your theme folder, then that text will render next to your theme when a user uses the command `/connect4 themes`. Only the first 200 characters will be displayed.  

The theme files that created the assets can be stored in the directory `raw_assets/connect4/`.  

#### Board
_Required_  
Filename: `board.png`  
Width: `430px`  
Height: `370px` (actual board size), can be taller if some type of header is wanted, but the board must start in the bottom left.  
From the bottom left, the pieces are 10px to the right and 10px from the bottom. This repeats until you get a 7 wide and 6 heigh board (creating the above dimensions).

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
</details>


<details>
  <summary>Mastermind</summary>

### Assets

In the folder `src/mastermind/assets`, create a theme folder, i.e. `src/mastermind/assets/classic` Inside that folder you will need to put the following assets for your theme. All assets must be png format to allow for transparency.  
If you add a file called `about.txt` into your theme folder, then that text will render next to your theme when a user uses the command `/mastermind themes`. Only the first 200 characters will be displayed.  

The theme files that created the assets can be stored in the directory `raw_assets/mastermind/`.  


### **hole.png**
This is a single peg hole block. Should be square to work best. The default theme uses a 60px by 60px canvas for this asset.


### **row_sep.png**
This is the separator between each row of guesses. Must be the same width as the `hole.png` asset, but the height is up to you.

### **peg-[0-5].png**
These are the pegs that the user plays with. The canvas must be the same size as used in the `hole.png` asset.  
This game has 6 color options, so name 6 pegs from `peg-0.png` ... `peg-5.png` 

### **colors.csv**
This is a file that will let the game know what color each peg is called. These names are used to create the buttons the player uses.  
An example of this file would be:
```csv
0,White
1,Black
2,Green
3,Red
4,Yellow
5,Blue
```

### **peg-[bw].png**
These pegs are used as feedback. The canvas must be the same size as used in the `hole.png` asset.  
The peg `peg-b.png` means that a players peg is in the correct color and position, and the peg `peg-w.png` means that a peg is the correct color, but wrong position.

</details>



# Running on your own server

<details>
  <summary>How to self host this bot</summary>

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

- `/mastermind`  
    Set the Request url to be `https://YOUR_DOMAIN/slack/mastermind`.   


#### Interactive Components
Enable and add the Request Url to be `https://YOUR_DOMAIN/slack/interactive`  

#### For slack oauth
Set up a redirect url: `https://YOUR_DOMAIN/slack/oauth`

## Running the server
Run the api server: `gunicorn server:api -w 2 --reload`
</details>
