# Quiz Game

## Description

1. When starting a game, the player chooses how many cards they want to guess for this game. They can choose from 5 up to half the total size of the set of cards.

2. The game shows the player each card image one at a time, and asks them to pick the correct answer from a list of 5 (displayed alphabetically). The possible answers are drawn randomly from the full list of answers for the complete set of cards, always including the correct answer for the current card.

3. The game then shows the player whether their guess was right or not, and moves on to the next card.

4. At the end, the game shows how many cards were guessed correctly (_e.g._ 16 out of 20, 80%). The player is then given the option to start a new game.

## Technical Requirements

1. The player should not need to log in. Each browser session should have a cookie to track the state of the current game.

2. The set of cards (each with an image and a correct answer) is to be obtained from an AWS S3 bucket containing image files, and one JSON file containing the list of cards, each with an image filename and a correct answer string.

3. The game should be hosted by a Docker container, which when running listens on the HTTP/HTTPS ports.

4. The game's back-end code, running in the container, should be Python 3, using FastAPI for the web framework with FastAPI's built-in SessionMiddleware for signed cookie-based session management. FastAPI's StaticFiles should be used to serve frontend assets and cached images. Card images should be downloaded from S3 to a local cache on application startup for better performance.

5. The game's front-end code, running in the player's browser, should use Tailwind for CSS. It needs to be mobile-friendly (work in a phone-sized form factor).

6. The dependencies needed by all the game code (_i.e._ Python packages, the specific version of Python being used, etc.) should have their versions controlled, so that upgrading to a later version requires a change to some version configuration file.
