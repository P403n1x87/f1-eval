# F1 Evaluation Race Data Recorder

Tool to collect evaluation race data from all the drivers. To have SteamID
appearing in the data, players should set `Show player names` to `On` in the
`Telemetry Settings`. This will make identification a bit easier.


## Installation

The application requires Python >= 3.8 to work.

~~~
pip install pipx
pipx install git+https://github.com/p403n1x87/f1-eval
~~~

## Usage

Simply run 

~~~
f1-eval
~~~

before the beginning of the session and let it collect data. At the end of the
session, data will be written in the current working directory.
