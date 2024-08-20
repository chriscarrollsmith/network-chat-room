# Program Flow

We are going to iteratively build up a natural language description of our program flow. We will look at one file at a time and only consider the code in that file.

The program has three entry points: the `app.py` file in the `client` module, the `server.py` file in the `server` module, and an `agent.py` file in the agent folder (for spinning up an automated user agent for testing).

## Logger configuration

The first thing in each entrypoint is a function call to `configure_logger` and assignment of a `logging.getLogger()` result to a `logger` variable. The `configure_logger` function is defined in `utils/logger.py`.

This function first creates a `root` logger set to log messages at the `logging.DEBUG` level and adds a `logger.StreamHandler` to it. It also creates and adds a `logging.Formatter` that includes the timestamp, name, log level, and message.

The function then creates and adds a `queue.Queue` with -1 maxsize (no limit) and a `logging.handlers.QueueHandler` that uses the queue as a buffer. It also creates and starts a `logging.handlers.QueueListener`. Under the hood, the `QueueHandler` will push log records to the queue, and the `QueueListener` will pop them off and pass them to the `StreamHandler`.

Since `logging.Logger` instances are singletons, we don't return the logger from this function. We run it once at the entrypoint, and all subsequent calls to `logging.getLogger` will inherit the configuration from the root logger.

## Server initialization

When we start the server with `python -m server.server`, it initializes a `socketserver.ThreadingTCPServer` instance that listens for incoming connections on 0.0.0.0:8888 until the server errors or is manually stopped by a keyboard interrupt, at which point it logs a message and closes the server. When initializing the `socketserver.ThreadingTCPServer` server, it passes a `Handler` class (which inherits from `socketserver.BaseRequestHandler`) to the constructor. This class contains methods for managing client connections and handling authentication, chat messages, and file transfers.

The `socketserver.ThreadingTCPServer` will spin up a new thread and a separate `Handler` instance for each client connection. Class variables (not to be confused with instance variables) are used for synchronization across threads. A `clients_lock` class variable is used as a context manager for thread-safety when accessing the `clients` dictionary, which is a class variable mapping usernames to `Handler` instances. Additionally, the class has a `user_manager` (an instance of `UserManager`) for storing and accessing user records and `chat_history` (an instance of `ChatHistory`) for storing and accessing chat logs. It also defines a constant `max_buff_size` of 1024 (1 KB) as the maximum buffer size for receiving data.

The Handler class's `setup` method creates empty `user`, `file_peer`, and `authed` instance variables for tracking the current user, the file transfer peer, and the authentication status of the user. This special named method is called by `socketserver.ThreadingTCPServer` when setting up a new thread upon client connection (so you don't have to override the `__init__` method).

> ### UserManager initialization
>
> The `UserManager` class is responsible for server-side management of user records. It has methods for registering and validating users and saving and loading user records to and from a `users.dat` file.
>
> The `__init__` method of `UserManager` creates a `threading.lock` for thread safety. It also creates a `users` instance variable for storing the `dict[str, str]` mapping of usernames to passwords, and calls the `load_users` method to load this `users` dictionary from the `users.dat` file. 
>
> `load_users` opens the `users.dat` file in binary mode and loads the `users` dictionary from the file using `pickle.load` for deserialization. If the file does not exist, it creates an empty dictionary.
>
> ### ChatHistory initialization
>
> The `ChatHistory` class is responsible for server-side management of chat logs. It has methods for saving and loading chat logs to and from a `history.dat` file.
>
> Its `__init__` method creates a `threading.lock` for thread safety. It also creates a `history` instance variable for storing the `dict[tuple[str, str], list[tuple[str, str, str]]]` mapping of chat identifiers (username pairs) to chat logs (a list of tuples, each containing a sender, a timestamp, and a message). It calls the `load_history` method to load this `history` dictionary from the `history.dat` file.
>
> `load_history` opens the `history.dat` file in binary mode and loads the `history` dictionary using `pickle.load`. If the file does not exist, it creates an empty dictionary.

## Client initialization

**TODO: Update this section to reflect the new client architecture**

When we start the client with `python -m client.app`, it creates an instance of the `Client` class at 127.0.0.1:8888.

The `__init__` method of the `Client` class creates `UIManager`, `NetworkManager`, `ChatManager`, and `FileManager` instances and assigns them to the `ui_manager`, `network_manager` and `file_manager` attributes, respectively:

> ### UIManager initialization
>
> The `UIManager` class is responsible for managing the user interface of the client. It has methods for creating and managing the login and main windows.
>
> The `__init__` method of `UIManager` simply creates empty `login_window` and `main_window` instance variables for storing the `Optional[LoginWindow]` and `Optional[MainWindow]` instances, respectively.
>
> ### NetworkManager initialization
>
> The `NetworkManager` class is responsible for client-side management of the network communication between the client and the server. It has methods for connecting to the server, sending messages, and handling file transfers.
>
> The `__init__` method of `NetworkManager` takes the `host` and `port` as arguments and saves them as instance variables. It then creates an empty `socket` (`socket.socket`) instance for the client and sets the `connected` instance variable to `False`. It also sets `max_buff_size` to 1024 (1 KB) and creates an empty `receive_thread` instance variable for storing the `threading.Thread` instance that will handle incoming messages from the server. Finally, it creates an `event_handlers` instance variable for storing the event handlers (`dict[str, list[Callable]]`) for each event. The variable is initialized with a handler for the "unknown" event type that logs an error message.
>
> ### ChatManager initialization
>
> The `ChatManager` class is responsible for managing the chat messages between users. It has methods for sending and receiving chat messages, as well as updating the chat history.
>
> Its `__init__` method takes the `network_manager` as an argument and saves them as instance variables. It also creates an empty `current_session` instance variable for storing the `Optional[str]` peer username of the current chat session.
>
> ### FileManager initialization
>
> The `FileManager` class is responsible for managing the file transfers between users. It has methods for sending and receiving files, as well as updating the chat history.
>
> Its `__init__` method takes the `network_manager` as an argument and saves them as instance variables. It also creates empty `_filename`, `_filename_short`, and `_file_transfer_pending` instance variables for storing the filename, the file basename, and the file transfer pending status, respectively.

## Client.run

When initialization of `Client`is complete, the client entrypoint calls the `run` method of the `Client` class. 

The `run` method first calls the `connect` method on the `NetworkManager` to connect to the server at 127.0.0.1:8888 and raises an error if the connection fails. The `connect` method does the following:

> ### NetworkManager connection
>
> It creates a streaming IPv4 `socket.socket` instance and connects it to the server host and port. 
>
> If the connection is successful, it sets the `connected` instance variable to `True`.

If the connection fails, `run` displays an error message box and returns `None`; otherwise it calls the `show_login` method of the `ui_manager` to start the login window loop. It passes the `network_manager` as an argument and assigns the return value to the `login_successful` variable.

If the `login_successful` variable is `True`, it calls the `show_main` method of the `ui_manager` to start the main UI window loop. It passes the `network_manager` and `file_manager` as arguments.

After starting the main window loop, `run` uses the `NetworkManager`'s `add_event_handler` method to register some `UIManager` methods as event handlers for each event type ("receive_message", "update_user_list", "file_request"). (Registering the handlers in a separate step after initialization prevents circular imports between the `NetworkManager` and `UIManager`.)

## Client login window loop

The `show_login` method of the `UIManager` class initializes a `LoginWindow` instance, passing our connected `network_manager` as an argument, and assigns it to the `login_window` instance variable of `ui_manager`.

The `LoginWindow`'s `__init__` method saves the `network_manager` as an instance variable and sets a `login_successful` instance variable to `False`. It then constructs a non-resizable, 300x180 "top level" `tkinter.Tk` widget titled "Login" with two string variables, `username` and `password`, for the username and password fields. It constructs and places these fields (`tkinter.Entry` widgets) and corresponding labels (`tkinter.Label`). It also constructs and places "Login" and "Register" buttons (`tkinter.Button`), which call the `handle_login` and `handle_register` methods of the `NetworkManager`, respectively.

**TODO: Update description of UI construction; add some detail on `Frame` and `pack`**

After initializing the window, the `show_login` method calls the window's `run_login_loop` method. `run_login_loop` calls the window's `mainloop` method (a tkinter method that listens for events and dispatches the appropriate handlers) and then destroys the window after the loop exits. It returns the `login_successful` instance variable.

**TODO: Update the following description of auth flow**

The two handler methods, `handle_login` and `handle_register`, are responsible for getting the username and password from the `username` and `password` fields, sending them to appropriate network_manager method (`login` or `register`) for communication with the server, and displaying a success or failure message box to the user. `login` additionally sets the `login_successful` instance variable to `True` and exits the event loop by calling the tkinter window's `quit` method if the server indicates a successful login.

> ### `NetworkManager` `register` method
>
> The `register` method of `NetworkManager` calls the `send` method of the same class, passing it a dictionary that includes "username", "password", and "command" keys. "command" is set to "register" to indicate that the client is requesting to register a new user account. We then call `receive` and assign the return value to the `response` variable. If the resonse is non-empty and its "response" key is "ok", the user is registered successfully and the method returns `True`. Otherwise, it returns `False`.
>
>> #### `NetworkManager` `send` method
>>
>> The `send` method checks if `connected` instance variable is `False` or `socket` is `None`, in which case it logs a `ConnectionError` and calls `close` (which cleans up any socket by calling `socket.socket.close` and any `receive_thread` by calling `threading.Thread.join`).
>>
>> Otherwise, it calls `encryption.utils.send`, passing the `socket` and payload as arguments. It returns `None`.
>>
>> #### `NetworkManager` `receive` method
>>
>> The `receive` method of `NetworkManager` logs a ConnectionError and calls `close` to clean up the socket and thread if `connected` is `False` or the `socket` is `None`. Otherwise, it calls `encryption.utils.receive`, passing the `socket` and `max_buff_size` instance variables as arguments. It returns the received data as a dictionary (or logs any JSON decode or other error and returns `None`).
>
> ### `NetworkManager` `login` method
>
> The `login` method of `NetworkManager` calls the `send` method, passing it a dictionary with "username", "password", and "command" set to "login". We then call `receive` and assign the return value to `response`. If the resonse is non-empty and its "response" key is "ok", the NetworkManager's username instance variable is set for the current session, the `start_receive_loop` method is called to start listening for server messages that will trigger UI updates for the main window, and the method returns `True`. Otherwise, it returns `False`.
>
>> #### `NetworkManager` `start_receive_loop` and `_receive_loop` methods
>>
>> The `start_receive_loop` method of `NetworkManager` does nothing if `receive_thread` is already running. Otherwise, it creates a new `threading.Thread`, passing `_receive_loop` as the target, and assigns it to the `receive_thread` instance variable. It then starts the thread.
>>
>> The `_receive_loop` method of `NetworkManager` is a `while` loop that continuously calls the `encryption.utils.receive` function, gets the event type from the "command" key of the received data, gets the handler list for the event type from the `event_handlers` instance variable, and calls each handler in sequence with the received data as an argument. It returns `None`.

## Encryption utility functions

The `send` and `receive` methods call some utility functions from `utils/encryption.py` that are shared by both the client and server, so this is a good place to explain how those functions work. These workhorse functions will be used throughout the application, not just for `login` and `register`, but this explanation will not be repeated, so you may want to come back and review it again later to understand the program flow of the main window loop.

### `send` and `encrypt` functions

`send` takes a `socket` and a `data_dict` as arguments. It first calls `generate_key`, which generates and returns a 32-byte random binary encryption key using `os.urandom(32)`. Then it converts the dictionary to a UTF-8 encoded JSON string using `json.dumps`. Then it passes the `data` and `key` to `encrypt`. 

`encrypt` generates a 16-byte random initialization vector (IV) and initializes an empty byte array. It then loops through the bytes in `data`, using the caret XOR operator and floor division to double-encrypt the data using the key and IV. It then base64 encodes the encrypted data using `base64.b64encode`. Finally, it returns the encoded and encrypted data along with the IV.

`send` then concatenates the key, IV, and encrypted data and assigns the result to `data_to_send`. Next, it calls `pack`, which prepends a 2-byte unsigned big-endian integer representing the length of `data_to_send` using `struct.pack` and returns the packed data. Finally, `send` sends the packed bytes to the server using `socket.socket.sendall`.

### `receive` and `decrypt` functions

`receive` takes a `socket` and `max_buff_size` as arguments. It first initializes an empty `bytes` variable called `data`. It then calls `socket.socket.recv(2)` to get the length prefix (the first two bytes) from the iterator. If it fails to get a two-byte length prefix, it raises a `ConnectionError`.

It then calls `struct.unpack` to unpack the length prefix into an integer named `surplus`. Then, with a five-second timeout set, it enters a while loop that continues until `surplus` is zero. The loop calls `socket.socket.recv` to get the next chunk of data, passing as an argument either `max_buff_size` or `surplus`, whichever is smaller, to get the next chunk of data. The received chunk is then added to `data` and its length is subtracted from `surplus`. A `ConnectionError` is raised if the received data is empty (e.g., because the connection timed out).

`receive` then extracts the key (first 32 bytes of `data`), IV (next 16 bytes), and encrypted data (remaining bytes) and assigns them to `key`, `iv`, and `encrypted_data`, respectively. Then it calls `decrypt` with `encrypted_data`, `key`, and `iv`. 

`decrypt` base64 decodes the encrypted data using `base64.b64decode`, initializes an empty byte array, and then loops through the bytes in `encrypted_data`, using the caret XOR operator and floor division to double-decrypt the data using the key and IV. It then returns the decrypted data.

Finally `receive` deserializes the decrypted JSON string using `json.loads` and returns the decrypted data as a dictionary.

## Server-side authentication handling

**TODO**

## Main window loop

**TODO**

The `show_main` method creates a `threading.Thread` instance to handle incoming messages from the server, and assigns it to the `receive_thread` instance variable. The `_receive_loop` method of the `NetworkManager` class is passed as the target for the thread, and the thread is started.

The `_receive_loop` method of the `NetworkManager` class is a daemon thread that runs in the background and continuously listens for incoming messages from the server. It uses the `receive` method of the `NetworkManager` to receive messages and update the UI accordingly.