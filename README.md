# Network Chat Room

A Python-based network chat room application using Tkinter for GUI and sockets for network communication. Based on [socket-chat-room](https://github.com/rihothy/socket-chat-room) by rihothy.

## Purpose

- Learn how to use Python's Tkinter module for building GUI applications.
- Learn how to use Python's socket module for TCP data transmission.
- Learn how to implement basic XOR encryption with an initialization vector.
- Learn how to implement a multi-threaded server in Python without a third-party library.
- Learn how to implement strict typing with `mypy`.

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