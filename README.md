# Network Chat Room

A Python-based AIM (AOL Instant Messenger)-style desktop chat room application, based on [rihothy](https://github.com/rihothy)'s [socket-chat-room](https://github.com/rihothy/socket-chat-room), using Tkinter for GUI and sockets for network communication.

## Purpose

I mostly created this project for educational purposes: 

- Learn to use Python's Tkinter module for building GUI desktop applications.
- Learn to use Python's socket module for TCP data transmission.
- Learn to implement a multi-threaded server and event system in Python without a third-party library.
- Learn to implement basic XOR encryption with an initialization vector.
- Learn to implement compile-time static type checking with `mypy`.
- Submit as my final project for the HarvardX course ["CS50's Introduction to Computer Science"](https://learning.edx.org/course/course-v1:HarvardX+CS50+X/home).

However, I'm also envisioning a practical use for this project: having autonomous AI agents running in Docker containers and using the chat app to update them on my progress (so they can encourage me to keep working), and they in turn can update me on their progress (so I can give them directions and advice to coordinate their work).

You can find a starter template for building chat room-connected AI agents in the [network-chat-room-agent](https://github.com/chriscarrollsmith/network-chat-room-agent) repository.

## Features

- GUI built with Tkinter
- Concurrent request handling on the server
- User registration and login functionality
- Global chat for all users
- One-on-one private chat
- File sharing between users
- Chat history storage and retrieval
- Data encryption using XOR algorithm with an initialization vector

## Running locally

To run the application locally, you will need [git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git), [Python 3.12](https://www.python.org/downloads/release/python-3120/) and the `poetry` package manager installed. You can install `poetry` by following the instructions at [python-poetry.org](https://python-poetry.org/docs/#installing-with-the-official-installer).

Once you have Python and `poetry` installed, you must clone the repo and install the package:

1. Clone the repo:
```bash
git clone https://github.com/chriscarrollsmith/network-chat-room.git
```

2. Navigate into the folder:
```bash
cd network-chat-room
```

3. Install the package:
```bash
poetry install
```

4. Copy the .example.env file to .env:
```bash
cp .example.env .env
```

Then you can run the server and client:

4. Start the server:
```bash
poetry run python -m server.server
```

5. Launch the client:
```bash
poetry run python client.client
```

## Usage

The client GUI will open in a new window. The interface is quite simple:

1. Use the "register" button to register a new account.

2. Login with the "login" button.

3. Select users from the list for private chats or use the global chat.

4. Send files using the "send file" button.

Obviously you will need someone to chat with. You can run multiple clients on the same machine by opening multiple terminal windows and running the client script in each one. You can also run the client on different machines on the same network by changing the `SERVER_HOST` variable in the client script to the IP address of the server machine (although you will need to allow incoming connections on the server machine's firewall).

Alternatively, you can add AI agents to the chat room. Follow the instructions in the [network-chat-room-agent](https://github.com/chriscarrollsmith/network-chat-room-agent) repo for adding an agent.

## Alternative workflow: run locally with Docker

Running in Docker is good practice when running any code from the Internet, not only because it helps ensure a reproducible build, but also because it provides a layer of isolation around the application to help protect your system from any unsafe code. It's fairly easy to run the network-chat-room server in Docker, but unfortunately the client is harder because it uses a GUI, and Docker containers don't normally have access to the host's GUI.

### Running the server in Docker

So before you get started, you should find and install the Docker Desktop application for your operating system at [Docker.com](https://www.docker.com/).

Once you have Docker Desktop installed, you can either clone the repo and deploy with docker-compose, or skip the clone and deploy directly from the GitHub repo.

1. Clone the repo and navigate into the folder (optional):
```bash
git clone https://github.com/chriscarrollsmith/network-chat-room.git
cd network-chat-room
```

2. Build and run with docker-compose:
```bash
docker-compose up server --build
# or
docker-compose -f https://raw.githubusercontent.com/chriscarrollsmith/network-chat-room/main/docker-compose.yml up server --build
```

This will start the server service inside a Docker network named `network_chat_room`.

### Running the client in Docker

You'll need an "X server" to make the client work in Docker. If you want to go down this rabbit hole, I try to provide some guidance in this section; otherwise you can always run the server in Docker but follow the instructions in a previous section to run the client directly on the host.

Note that while I've tried to provide for this use case, I haven't actually tested it, so I can't guarantee it will work. If you try it and run into issues, please let me know by opening an issue.

The most popular X server is VcXsrv, which you can download from [sourceforge.net](https://sourceforge.net/projects/vcxsrv/), but honestly I can't personally vouch for it, because I haven't reviewed the code. If you do go this route, you'll need to start the X server before running the client container, and set it to 'multiple windows', 'start no client', and 'display number 0'.

Then you can run the client container using:

```bash
docker-compose up client --build
```

## Development

I'm using `poetry` to manage the project and `mypy` for type checking. To perform type checks, run:

```bash
poetry run mypy .
```

Feel free to submit pull requests or open issues to improve the project.

## Note

I titled this repo `network-chat-room`, not `internet-chat-room`, even though you could technically host it over the Internet, because this repo is *not* production-ready. In particular, the encryption and auth used here is a toy implementation and is *not* secure. We are sending the decryption key as plaintext with every API call. Frankly, the only real security here is that the server is not publicly accessible from the Internet.

For production use, consider implementing:

- Secure key exchange protocol such as Diffie-Hellman, RSA, PSK, SSL/TLS, etc.
- Stronger encryption algorithm such as AES-256, Blowfish, Twofish, etc.
- Hashing stored user data with a secure hashing algorithm
- Database for user and chat history storage
- Additional features and UI improvements
- Compile a distributable executable for the client with `pyinstaller` or, alternatively, drop the tkinter GUI and build a browser-based client interface with JavaScript
