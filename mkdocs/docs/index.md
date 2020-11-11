# Welcome to Alpaca Proxy Agent

```py

   _   _                           ___                         _                    _   
  /_\ | |_ __   __ _  ___ __ _    / _ \_ __ _____  ___   _    /_\   __ _  ___ _ __ | |_ 
 //_\\| | '_ \ / _` |/ __/ _` |  / /_)/ '__/ _ \ \/ / | | |  //_\\ / _` |/ _ \ '_ \| __|
/  _  \ | |_) | (_| | (_| (_| | / ___/| | | (_) >  <| |_| | /  _  \ (_| |  __/ | | | |_ 
\_/ \_/_| .__/ \__,_|\___\__,_| \/    |_|  \___/_/\_\\__, | \_/ \_/\__, |\___|_| |_|\__|
        |_|                                          |___/         |___/                

```

This is a project to help users of [Alpaca](https://alpaca.markets) to execute more than one data websocket connections against their servers.

Right now you can only connect one websocket with your user credentials. if you want to run more than one algorithm, you can't.<br>
This project will help you achieve that. look at this illustration to get the concept

![alt text](resources/concept.png)

It doesn't matter which sdk you are using (python, js, go, c#) you can use this to achieve that.

## How to execute the docker container
You have 2 options:
- Using docker with image from docker hub (easiest)
- Cloning the repo and using docker/docker-compose to build and run this project locally(a bit more powerful if you want to edit the proxy code)

 
### Directly from docker hub
Nothing easier than that.
- Make sure you have docker installed
- make sure you have the updated image version by running this: `docker pull shlomik/alpaca-proxy-agent`
- Execute this command: `docker run -it -p 8765:8765 shlomik/alpaca-proxy-agent`<br>
note: You can change the port you're listening on just by doing this `-p xxxx:8765`
### Executing a local copy
- Clone the repo: `git clone https://github.com/shlomikushchi/alpaca-proxy-agent.git`
- Run this command locally: `docker-compose up`<br>
  It will build the image and run the container using docker-compose<br>
note: If you want to execute in edit mode do this: `docker-compose -f dev.yml up` <br>
You could then update `main.py` and execute it locally.

## Selecting the data stream source
Alpaca supports 2 data streams:
* Alapca data stream
* Polygon data stream<br>

If you are using this project I assume you know what these are and what are the differences.<br>
The default data stream is Alpaca. To select the Polygon data stream you need to set an environment variable called `USE_POLYGON` like so:<br>
>`docker run -p 8765:8765 -it -e USE_POLYGON=true shlomik/alpaca-proxy-agent`<br>

## Security
You are runngin a local websocket server. Make sure your IP is not accessible when you do (you probably shouldn't run this on public networks)<br>
SSL between your algo and the proxy is not supported (it runs locally). between the proxy-agent and the Alpaca servers we use wss
  


## Commands

* `mkdocs new [dir-name]` - Create a new project.
* `mkdocs serve` - Start the live-reloading docs server.
* `mkdocs build` - Build the documentation site.
* `mkdocs -h` - Print help message and exit.

## Project layout

    mkdocs.yml    # The configuration file.
    docs/
        index.md  # The documentation homepage.
        ...       # Other markdown pages, images and other files.
