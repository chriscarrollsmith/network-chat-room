# Program Flow

We are going to iteratively build up a natural language description of our program flow. We will look at one file at a time and only consider the code in that file.

The program has two entry points: the `app.py` file in the `client` module and the `server.py` file in the `server` module.

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

When we start the client with `python -m client.app`, it creates an instance of the `Client` class at 127.0.0.1:8888.

The `__init__` method of the `Client` class creates `UIManager`, `NetworkManager`, `ChatManager`, and `FileManager` instances and assigns them to the `ui_manager`, `network_manager`, `chat_manager`, and `file_manager` attributes, respectively:

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
> The `__init__` method of `NetworkManager` takes the `host` and `port` as arguments and saves them as instance variables. It then creates an empty `socket` (`socket.socket`) instance for the client and sets the `connected` instance variable to `False`. It also sets `max_buff_size` to 1024 (1 KB) and creates an empty `receive_thread` instance variable for storing the `threading.Thread` instance that will handle incoming messages from the server. Finally, it creates an empty `event_handlers` instance variable for storing the event handlers (`dict[str, list[Callable]]`) for each event.
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

If the `login_successful` variable is `True`, it calls the `show_main` method of the `ui_manager` to start the main UI window loop. It passes the `network_manager`, `chat_manager`, and `file_manager` as arguments.

After starting the main window loop, `run` uses the `NetworkManager`'s `add_event_handler` method to register some `UIManager` methods as event handlers for each event type ("receive_message", "update_user_list", "file_request"). (Registering the handlers in a separate step after initialization prevents circular imports between the `NetworkManager` and `UIManager`.)

## Client login window loop

The `show_login` method of the `UIManager` class initializes a `LoginWindow` instance, passing our connected `network_manager` as an argument, and assigns it to the `login_window` instance variable of `ui_manager`.

The `LoginWindow`'s `__init__` method saves the `network_manager` as an instance variable and sets a `login_successful` instance variable to `False`. It then constructs a non-resizable, 320x240 "top level" `tkinter.Tk` widget titled "Login" with two string variables, `username` and `password`, for the username and password fields. It constructs and places these fields (`tkinter.Entry` widgets) and corresponding labels (`tkinter.Label`). It also constructs and places "Login" and "Register" buttons (`tkinter.Button`), which call the `handle_login` and `handle_register` methods of the `NetworkManager`, respectively.

After initializing the window, the `show_login` method calls the window's `run_login_loop` method. `run_login_loop` calls the window's `mainloop` method (a tkinter method that listens for events and dispatches the appropriate handlers) and then destroys the window after the loop exits. It returns the `login_successful` instance variable.

The two handler methods, `handle_login` and `handle_register`, are responsible for getting the username and password from the `username` and `password` fields, sending them to appropriate network_manager method (`login` or `register`) for communication with the server, and displaying a success or failure message box to the user. `login` also sets the `login_successful` instance variable to `True` and exits the event loop by calling the tkinter window's `quit` method if the server indicates a successful login.

### `NetworkManager` `register` method

TODO

#### `NetworkManager` `send` method

TODO

#### `NetworkManager` `receive` method

TODO

### `NetworkManager` `login` method

TODO

#### `NetworkManager` `start_receive_loop` and `_receive_loop` methods

TODO

## Encryption utility functions

The `send` and `receive` methods call some utility functions from `encryption/utils.py` that are shared by both the client and server, so this is a good place to explain how those functions work. These workhorse functions will be used throughout the application, not just for `login` and `register`, but this explanation will not be repeated, so you may want to come back and review it again later to understand the program flow of the main window loop.

TODO

## Main window loop

The `show_main` method creates a `threading.Thread` instance to handle incoming messages from the server, and assigns it to the `receive_thread` instance variable. The `_receive_loop` method of the `NetworkManager` class is passed as the target for the thread, and the thread is started.

The `_receive_loop` method of the `NetworkManager` class is a daemon thread that runs in the background and continuously listens for incoming messages from the server. It uses the `receive` method of the `NetworkManager` to receive messages and update the UI accordingly.