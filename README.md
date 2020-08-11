# alpaca-proxy-agent
this is a project to help users of [alpaca](https://alpaca.markets) to execute more than one websocket connections against their servers.

right now you can only connect one websocket with your user credentials. if you want to run more than one algorithm, you can't.<br>
this project will help you achieve that. look at this illustration to get the concept

![alt text](resources/concept.png)

it doesn't matter which sdk you are using (python, js, go, c#) you can use this to achieve that.

## How to use
you have 2 options:
- using docker with image from docker hub (easiest)
- cloning the repo and using docker/docker-compose to build and run this project locally(a bit more powerful if you want to edit the proxy code)

 
### directly from docker hub
nothing easier than that.
- make sure you have docker installed
- execute this command: `docker run -p 8765:8765 shlomik/alpaca-proxy-agent`<br>
note: you can change the port you're listening on just by doing this `-p xxxx:8765`
### executing local copy
- clone the repo: git clone https://github.com/shlomikushchi/alpaca-proxy-agent.git
- run this command locally: `docker-compose up`<br>
  it will build the image and run the container using docker-compose
note: if you want to execute in edit mode do this: `docker-compose -f dev.yml up` <br>
you could then update `main.py` and execute it locally.

## Security
you are runngin a local websocket server. make sure your IP is not accessible when you do (you probably shouldn't run this on public networks)
  
