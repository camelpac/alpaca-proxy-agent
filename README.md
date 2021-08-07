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
This project will help you achieve that. Look at this illustration to get the concept

![alt text](resources/concept.png)

It doesn't matter which sdk you are using (python, js, go, c#) you can use this to achieve that.

## How to execute the docker container
You have 2 options:
- Using docker with the image from docker hub (easiest)
- Cloning the repo and using docker/docker-compose to build and run this project locally(a bit more powerful if you want to edit the proxy code)

 
### Directly from docker hub
Nothing easier than that.
- Make sure you have docker installed
- make sure you have the updated image version by running this: `docker pull camelpac/alpaca-proxy-agent`
- Execute this command (this will use the free account data stream(iex). read further to learn how to enable the sip data stream): `docker run -it -p 8765:8765 camelpac/alpaca-proxy-agent`<br>
note: You can change the port you're listening on just by doing this `-p xxxx:8765`
### Executing a local copy
- Clone the repo: `git clone https://github.com/camelpac/alpaca-proxy-agent.git`
- Run this command locally: `docker-compose up`<br>
  It will build the image and run the container using docker-compose<br>
note: If you want to execute in edit mode do this: `docker-compose -f dev.yml up` <br>
You could then update `main.py` and execute it locally.

## Available Arguments
There are a few env variables you could pass to your proxy-agent instance
* Data stream sip(paid account) or iex(free account)

You can do it like this:
- IS_PRO: if true use the sip data stream. if false, use the iex data stream. default value is false.

so you should execute this for the paid data stream:
```python
 docker run -p 8765:8765 -it -e IS_PRO=true camelpac/alpaca-proxy-agent
```
and you should execute this for the free data stream:

```python
 docker run -p 8765:8765 -it -e IS_PRO=false camelpac/alpaca-proxy-agent
```

## Security
You are running a local websocket server. Make sure your IP is not accessible when you do (you probably shouldn't run this on public networks)<br>
SSL between your algo and the proxy is not supported (it runs locally). between the proxy-agent and the Alpaca servers we use WSS
