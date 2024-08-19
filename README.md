# Network Chat Room

A Python-based AIM (AOL Instant Messenger)-style desktop chat room application, based on rihothy's[socket-chat-room](https://github.com/rihothy/socket-chat-room), using Tkinter for GUI and sockets for network communication.

## Purpose

I mostly created this project for educational purposes: 

- Learn to use Python's Tkinter module for building GUI desktop applications.
- Learn to use Python's socket module for TCP data transmission.
- Learn to implement a multi-threaded server and event system in Python without a third-party library.
- Learn to implement basic XOR encryption with an initialization vector.
- Learn to implement compile-time static type checking with `mypy`.
- Submit as my final project for the HarvardX course ["CS50's Introduction to Computer Science"](https://learning.edx.org/course/course-v1:HarvardX+CS50+X/home).

However, I'm also envisioning a practical use for this project: having autonomous AI agents running in Docker containers and using the chat app to update them on my progress (so they can encourage me to keep working), and they in turn can update me on their progress (so I can give them directions and advice to coordinate their work).

## Features

- GUI built with Tkinter
- Concurrent request handling on the server
- User registration and login functionality
- Global chat for all users
- One-on-one private chat
- File sharing between users
- Chat history storage and retrieval
- Data encryption using XOR algorithm with an initialization vector

## Implementation Details

### Encryption and Decryption
- Custom `encrypt` and `decrypt` functions using XOR encryption with an initialization vector (although in this simplified implementation, we're sending the key and IV as plaintext, which is totally insecure)

### Network Communication
- Socket-based data transmission with packet size prefixing

### User Management
- File-based user information storage
- Registration and authentication functions

### Chat History
- Storage and retrieval of chat history for all users

### Server
- Uses `socketserver.ThreadingTCPServer` with `socketserver.BaseRequestHandler` for handling concurrent connections
- Handles login, registration, user listing, and message routing

### Client
- Login and registration interface
- Main chat window with user list and chat history
- Socket connection for receiving server messages

## How to Run

1. Install the package:
```bash
poetry install
```

2. Start the server:
```bash
poetry run python -m server.server
```

3. Launch the client application:
```bash
poetry run python client.client
```

4. Use the login window to authenticate or register a new account.

5. After successful login, use the main chat window to communicate.

6. Select users from the list for private chats or use the global chat.

7. Send messages or files using the provided interface.

## Run with Docker

1. Build the Docker image:
```bash
docker build -t server-app .
```

2. Run the Docker container:
```bash
docker run -p 8888:8888 server-app
```

## Development

I'm using `poetry` to manage the project and `mypy` for type checking. To lint the project, run:

```bash
poetry run mypy .
```

Feel free to submit pull requests or open issues to improve the project.

## Note

This is a very basic implementation for educational purposes only. For production use, consider implementing:

- Secure key exchange protocol such as Diffie-Hellman, RSA, PSK, SSL/TLS, etc.
- Stronger encryption algorithm such as AES-256, Blowfish, Twofish, etc.
- Database for user and chat history storage
- Hashing stored user data with a secure hashing algorithm
- Enhanced error handling and input validation
- Comprehensive logging
- Additional features and UI improvements