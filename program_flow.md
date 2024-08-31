# Program Flow

We are going to iteratively build up a natural language description of our program flow. We will look at one file at a time and only consider the code in that file.

The program has two entry points: the `client.py` file in the `client` module and the `server.py` file in the `server` module.

## Logger configuration

The first thing each entrypoint does is load environment variables with `python-dotenv`, call the `configure_logger` function with the `LOG_LEVEL` environment variable as an argument, and assign the result of `logging.getLogger()` to a `logger` variable.

The `configure_logger` function is defined in `utils/logger.py`. This function first creates a `root` logger set to log messages at a level determined by the environment variable, and adds a `logger.StreamHandler` to it. It also creates and adds a `logging.Formatter` that includes the timestamp, name, log level, and message.

The function then creates and adds a `queue.Queue` with -1 `maxsize` (no limit) and a `logging.handlers.QueueHandler` that uses the queue as its buffer. It also creates and starts a `logging.handlers.QueueListener`. Under the hood, the `QueueHandler` will push log records to the queue, and the `QueueListener` will pop them off and pass them to the `StreamHandler`.

Since `logging.Logger` instances are singletons, we don't return the logger from this function. Rather, we run the `configure_logger` function once at the entrypoint, and all subsequent calls to `logging.getLogger` will inherit the configuration from the root logger.

## Server `RequestHandler` initialization

When we start the server with `python -m server.server`, it initializes a `socketserver.ThreadingTCPServer` instance that listens for incoming connections on 0.0.0.0:8888 until the server errors or is manually stopped by a keyboard interrupt, at which point it logs a message and closes the server. When initializing the `socketserver.ThreadingTCPServer` server, the entrypoint passes a `RequestHandler` class (which inherits from `socketserver.BaseRequestHandler`) to the constructor. 

Like the Python logger, `socketserver.ThreadingTCPServer` and `socketserver.BaseRequestHandler` follow the Borg/Monostate pattern. What that means in practice is that a new thread and `RequestHandler` instance will be spun up for each client connection (but never more than one per connection).

The `RequestHandler` class contains methods for managing client connections and handling authentication, chat messages, and file transfers. Class variables (not to be confused with instance variables) are used for synchronization across threads.A `clients_lock` class variable is used as a context manager for thread-safety when accessing the `clients` dictionary, which is a class variable mapping usernames to `Handler` instances. Additionally, the class has a `user_manager` attribute (an instance of `UserManager`) for storing and accessing user records, and a `chat_history` attribute (an instance of `ChatHistory`) for storing and accessing chat logs. It also defines a constant `max_buff_size` of 1024 (1 KB) as the maximum buffer size for receiving data.

While the class and its variables will be shared across all threads, instances and their variables will be unique to each thread. The `RequestHandler` class's `setup` method creates empty `username`, `file_peer`, and `authed` instance variables for tracking the username of the user connected to that instance, the username of any current file transfer peer, and the authentication status of the connected user. `setup` is a special named method called by `socketserver.ThreadingTCPServer` when setting up a new thread and `BaseRequestHandler` instance upon client connection (so you don't have to override the handler class's `__init__` method to define custom initialization logic).

> ### UserManager initialization
>
> The `UserManager` class is responsible for server-side management of user records. It has methods for registering and validating users and saving and loading user records to and from a `users.dat` file. When the class is imported, environment variables are loaded to get the location of the `STORAGE_DIR` where user records will be stored, and the directory is created if it doesn't exist already.
>
> The `__init__` method of `UserManager` creates a `threading.lock` for thread safety in performing file operations. Then it constructs the file path of the `users.dat` user data file in the storage directory. A `users` instance variable for storing the `dict[str, str]` mapping of usernames to passwords is initialized with a value returned from the `load_users` method. 
>
> `load_users` opens the `users.dat` file in binary mode and loads the `users` dictionary from the file using `pickle.load` for deserialization. If deserialization fails or the file does not exist, it logs a warning and returns an empty dictionary.
>
> ### ChatHistory initialization
>
> The `ChatHistory` class is responsible for server-side management of chat logs. It has methods for saving and loading chat logs to and from a `history.dat` file. When the class is imported, environment variables are loaded to get the location of the `STORAGE_DIR` where chat logs will be stored, and the directory is created if it doesn't exist already.
>
> Its `__init__` method creates a `threading.lock` for thread safety and constructs a `history_filepath` by adding `history.dat` to the storage dir. Then it initializes a `history` instance variable for storing the `dict[tuple[str, str], list[tuple[str, str, str]]]` mapping of chat identifiers (username pairs) to chat logs (a list of tuples, each containing a sender, a timestamp, and a message) with a value returned from the `load_history` method.
>
> `load_history` opens the `history.dat` file in binary mode and loads and returns the `history` dictionary using `pickle.load`. If deserialization fails or the file does not exist, it logs a warning and returns an empty dictionary.

## Client initialization

When we start the client with `python -m client.client`, it loads environment variables, gets the server IP and server port variables, and creates an instance of the `Client` class, passing the IP and port values to the constructor.

The `__init__` method of the `Client` class creates empty `login_window` and `main_window` instance variables for storing the `Optional[LoginWindow]` and `Optional[MainWindow]` instances, respectively.

It also creates `NetworkManager` and `FileManager` instances and assigns them to the `network_manager` and `file_manager` attributes. NetworkManager is passed the server IP and port, and FileManager is passed the NetworkManager instance.

> ### NetworkManager initialization
>
> The `NetworkManager` class is responsible for client-side management of the network communication between the client and the server. It has methods for connecting to the server, sending messages, and dispatching incoming server messages to event handlers.
>
> The `__init__` method of `NetworkManager` takes the `host` and `port` as arguments and saves them as instance variables. It then creates an empty `socket` (`socket.socket`) instance for the client. It also sets `max_buff_size` to 1024 (1 KB) and creates an empty `receive_thread` instance variable for storing the `threading.Thread` instance that will receive and handle incoming messages from the server.
>
> Finally, it creates an empty `username` instance variable for tracking the currently authenticated user and an empty `event_handlers` instance variable for storing the event handlers (`dict[str, list[Callable]]`) for each event.
>
> ### FileManager initialization
>
> The `FileManager` class is responsible for managing file transfers between users. It has methods for sending and receiving file data.
>
> Its `__init__` method takes the `network_manager` as an argument and saves them as instance variables. It also creates an empty `_file_transfer_pending` boolean instance variable to indicate whether a transfer is in progress, as well as `_filename` and `_filepath` instance variables for storing the filename and basename for any pending transfer.

## Client.run

When initialization of `Client`is complete, the client entrypoint calls the `run` method of the `Client` class. 

The `run` method calls the `connect` method on the `NetworkManager` to connect to the server the specified IP and port and displays a tkinter error messagebox and returns None if the connection fails. The `connect` method does the following:

> ### NetworkManager `connect` method
>
> It creates a streaming IPv4 `socket.socket` instance and connects it to the server host and port. 
>
> It calls the `start_receive_loop` method to start listening for server messages that will trigger UI updates for the main window.
>
> It then calls the `validate_connection_state` method with `should_be_connected=True`, which checks that the socket is truthy (connected) and the thread alive within a 5-second timeout. If validation fails, it logs and raises a `ConnectionError` (which is caught and re-raised by `connect`).

If the connection fails, `run` displays an error message box and returns `None`; otherwise it initializes the `LoginWindow` class, passing its constructor the `network_manager`, and assigns it to the `login_window` instance variable. Then it calls the `login_window`'s' `show` method and waits for it to return a boolean `auth_success` value.

If `auth_successful` is falsy, we return None; otherwise we initialize `MainWindow` with the `network_manager` and `file_manager` as arguments and assign it to a `main_window` instance variable, and then we call the `main_window`'s `show` method.

## Client receive loop

Most of the client-side magic happens in the `NetworkManager` class's receive loop. When the `connect` method calls `start_receive_loop`, it creates a new daemon `threading.Thread` instance with the `_receive_loop` method as the target and assigns it to the class's `receive_thread` instance variable. It then starts the thread.

The `_receive_loop` method is a `while` loop that continues as long as the `socket` is truthy (i.e., connected). The loop calls the `handle_receive_errors` method, passing it the `receive` function, and assigns the return value to the `data` dictionary.

>`handle_receive_errors` calls the `receive` function (from `utils.encryption`) passed to it and catches and logs any exceptions raised thereby. In the event of an exception, it calls the `close_connection` method to clean up the socket and thread (unless the exception is a non-fatal `JSONDecodeError`) and returns `None`; otherwise, it returns the received data.

When non-empty `data` is received, the `_receive_loop` method checks the value of its "type" key. This value is used as a key to retrieve a value (a list of `Callable`s) from the `event_handlers` instance variable. If we find such a list, we call each `Callable` in sequence with the received data as an argument. After the last handler is called, the loop continues to the next iteration.

Note that the receive loop is initially started with an empty handler dictionary; handlers are mounted and dismounted as the client opens and closes the login and main windows.

Note: in terms of flow control, the loop assumes that the `receive` method will not return until data is received or the socket is disconnected. That is, the assumption is that we only loop once per received server message. We also assume we don't need to worry about missing any messages during handler operations because `receive` is fetching server messages from a queue, not actually listening for and receiving them in real time.

The loop will stop (and the thread will exit) if (and only if) the `socket` is falsy or an error is raised in `receive` or any of the handlers. (So we need to be careful to catch and gracefully handle any handler exceptions we don't want to terminate the client, and also to disconnect the socket when we want the client to close or the `_receive_loop` to stop.)

### The `utils.encryption.receive` function

The functions in the `utils.encryption` module are the workhorses of the client-server communication, designed for reusability at both ends. We'll cover `receive` here and `send` later.

The `receive` function assumes the data has been sent by the server in a specific format: a 2-byte unsigned big-endian integer representing the length of the data, followed by a 32-byte encryption key, a 16-byte initialization vector (IV), and the data, which has been serialized to JSON and encrypted.

takes a `socket` and a `max_buff_size` as arguments. It first initializes an empty `bytes` variable called `data`. It then calls `socket.socket.recv(2)` with no timeout to get the length prefix (the first two bytes) of any incoming server message.

The behavior of `socket.socket.recv` is to block until it receives the requested number of bytes, the timeout (if any) expires, or the connection is closed. If the connection is closed, `recv` will return an empty `bytes` object. Thus, we next detect a closed connection by checking if the length prefix is empty. If it is, we raise a `ConnectionError` and exit the function.

Next, we call `struct.unpack` to convert the `length_prefix` from a C struct with `format=">H"` (unsigned short integer) to a Python integer named `surplus`.

Then, with a five-second timeout set, we enter a while loop that continues until `surplus` is zero. The loop calls `socket.socket.recv` to get the next chunk of data, passing as an argument either `max_buff_size` (or `surplus`, whichever is smaller), to get the next (or last) chunk of data. The received chunk is then added to `data` and its length is subtracted from `surplus`. A `ConnectionError` is raised if the received data is empty (e.g., because the connection timed out).

Finally, we extract the key (first 32 bytes of `data`), IV (next 16 bytes), and encrypted data (remaining bytes) and assign them to `key`, `iv`, and `encrypted_data`, respectively. We then call `decrypt` with `encrypted_data`, `key`, and `iv`, deserialize the decrypted JSON string using `json.loads`, and return the decrypted data as a dictionary.

> #### `utils.encryption.decrypt` function
>
> The `decrypt` function takes `data`, `key`, and `iv` (all `bytes`) as arguments. It base64 decodes the encrypted data using `base64.b64decode`, initializes an empty byte array, and then loops through the bytes in `encrypted_data`, using the caret XOR operator to double-decrypt the data using the key and IV (which are repeated as many times as necessary with the help of the mod operator). We then return the decrypted data.

## Client login window initialization

When the `run` method of the `Client` initializes the LoginWindow instance with the `network_manager` as an argument, the `__init__` method of that class assigns the `network_manager` to an instance variable. It then creates a `tkinter.Tk` instance, assigns it to `window`, and sets the window layout attributes: `title` to "Login", `minsize` to 300x180, and `resizable` to `True`.

It then initializes the `authed` instance variable to False and creates two `tkinter.StringVar` instances (with `window` as the parent) to hold user inputs to the username and password fields.

Next, we create four frames (`tkinter.Frame` instances) for the window: `main_frame` to hold the other frames, `username_frame` and `password_frame` to hold the username and password fields, and `button_frame` to hold the login and register buttons. The `main_frame` is initialized with the `window` as its parent (first argument), and the `username_frame`, `password_frame`, and `button_frame` are initialized with the `main_frame` as their parent.

The `main_frame` is initialized with 20 pixels of interior padding on all sides, and then `pack`ed with fill set to `tkinter.BOTH` and expand set to `True`. This will cause the frame to fill the window in both the x and y directions and expand to fill any extra space.

The `username_frame`, `password_frame`, and `button_frame` are each `pack`ed to fill the x direction. The `username_frame` and `password_frame` are also `pack`ed with 5 pixels of exterior y padding, while the `button_frame` is `pack`ed with 20.

The `username_frame` contains a `tkinter.Label` with the text "Username" and `width` 10, `pack`ed to the left side of the frame, and a `tkinter.Entry` with the `textvariable` set to the `username` instance variable and `pack`ed to the right side of the frame, with `expand` set to `True` and `fill` set to `tkinter.X`.

The `password_frame` is similar, but with text "Password", `textvariable` set to the `password` instance variable, and `show` set to `*` to hide the password text.

As for the `button_frame`, it contains two `tkinter.Button` instances: one with the text "Login" and the `command` set to the `login` method of the `LoginWindow`, and the other with the text "Register" and the `command` set to the `register` method of the `LoginWindow` instance. Both buttons are `pack`ed to the right side, with 5 pixels of exterior x padding and `expand` set to `True` to fill any extra space.

Once this tkinter interface is constructed, `__init__` calls `window`'s `bind` method to bind Return key presses to the `login` method.

Finally, `__init__` call's the `network_manager`'s `add_event_handler` method to add the `handle_login` and `handle_register` methods of the `LoginWindow` instance as event handlers for the "login_result" and "register_result" events, respectively.

If an error occurs during any of these initialization steps, `__init__` shows an error messagebox and then raises the error to the calling context (the `run` method of `Client`) to terminate the program.

> ### The `add_event_handler` method of `NetworkManager`
>
> The `add_event_handler` method of `NetworkManager` takes an `event_type` and a `handler` as arguments. If the `event_handlers` dictionary does not already contain the `event_type` key, the key's value is first initialized with an empty list. Having made sure we have a list to append to, we append the `handler` to the list of handlers for the `event_type`.

## Showing the client login window

The `LoginWindow`'s `show` method, called by `Client.run` after window initialization is complete, calls the window's `mainloop` method (a tkinter method that listens for and handles UI events). The behavior of this method is to block until the window is closed by the user or the `quit` method is called on the window.

Once the window is closed, `show` calls the `network_manager's` `clear_event_handlers` method to remove the event handlers that deal with login and registration results. It also calls the `window`'s `destroy` method to close the window. If `authed` is `False`, it also calls the `network_manager's` `close_connection` method to clean up the socket and thread. If errors occur during these teardown steps, they are collected and raised to the calling context (the `run` method of `Client`), and a tkinter messagebox displays a generic error message. Otherwise, we return the value of the `authed` instance variable.

## Client-side authentication request handling

When the user clicks the "Login" or "Register" button in the `LoginWindow`, the `login` or `register` method is called. Each method gets the username and password from the `username` and `password` fields, calls the `network_manager` `send` method to pass the request to the server, and displays a success or failure messagebox to the user.

The payload sent to `send` is a dictionary with a "type" key set to "login" or "register" and "username" and "password" keys set to the user's input.

> ### `NetworkManager` `send` method
>
> The `send` method checks if the `socket` is truthy. If not, it raises a `ConnectionError`. If so, it calls `encryption.utils.send`, passing the `socket` and payload as arguments.
>
> If an error occurs, we call `close_connection` to log the error, clean up any socket and `receive_thread`, and raise the error to the calling context (some `LoginWindow` or `MainWindow` method), which will be responsible for handling it gracefully.

### The `utils.encryption.send` function

The `send` function takes a `socket` and a `data_dict` as arguments. It first calls `generate_key`, which generates and returns a 32-byte random binary encryption key using `os.urandom(32)`. Then it converts the dictionary to a UTF-8 encoded JSON string using `json.dumps`. Then it passes the `json_data` and `key` to `encrypt`, assigning the result to `encrypt_result`.

> #### `utils.encryption.encrypt` function
>
> `encrypt` generates a 16-byte random initialization vector (IV) and initializes an empty `bytearray` named `encrypted`. It then loops through the bytes in `data`, using the caret XOR operator to double-encrypt the data using the key and IV, and the percent-sign mod operator to repeat the key and IV as many times as necessary. It then base64 encodes the encrypted data using `base64.b64encode`. Finally, it returns the encoded data along with the IV.

`send` then concatenates the key, IV, and encrypted data and assigns the result to `data_to_send`. Next, it calls `pack`, which prepends a 2-byte unsigned big-endian integer representing the length of `data_to_send` using `struct.pack` and returns the packed data. Finally, `send` sends the packed bytes to the server using `socket.socket.sendall`.

## Client-side authentication response handling

In addition to methods for sending authentication requests to the server, `LoginWindow` also has handlers for the server's responses to those requests. (These methods are added as event handlers to the `network_manager` in the `LoginWindow`'s `__init__` method and removed in the `show` method after the `mainloop` ends.)

When the server sends a response to a login or registration request, the `NetworkManager`'s `_receive_loop` checks the reponse's "type" key and dispatches events to the corresponding handler. If the authentication handlers have been correctly mounted, "login" and "register" responses will trigger the `handle_login_result` and `handle_register_result` methods of the `LoginWindow` instance, respectively.

Both methods check the "response" key to see if the value is "ok". If it is, `login` sets the `authed` instance variable to `True`, gets the username for the current session from the `network_manager`'s `username` instance variable, and calls `quit` on the `window` to end the `mainloop` (so `show` will clean up the window and return the `authed` result to the `run` method of `Client`). `register`, on the other hand, merely displays a success messagebox.

If the "response" key is not "ok", both methods call `handle_authentication_failure`, which displays a descriptive error messagebox to the user. If "response" was "fail", the "reason" key will contain a string describing the failure; otherwise we display a generic error message.

## Server-side authentication request handling

The `socket.socket.BaseRequestHandler` class provides an API for defining a `setup` method called upon initialization, a `handle` method called to handle client requests, and a `finish` method called when the client connection is closed. It also provides a `self.request` attribute that is a socket object representing the client connection. We already discussed our custom `setup` method for the `RequestHandler` class above; here we'll look at the `handle` method.

### The `handle` method of the `RequestHandler` class

The `handle` method of the `socket.socket.BaseRequestHandler` is typically implemented as an infinite `while True` loop that reads data from the client socket with `socket.recv` and processes it. If the client disconnects, `socket.recv` raises a `ConnectionResetError`, which terminates the loop. A `finally` block in `BaseRequestHandler` then calls `finish` to run any cleanup tasks.

In my implementation, I tried to handle this a bit more gracefully by using `while self.request` as the loop condition (mostly because I find it unintuitive to ever use `while True`, rather than because this actually changes the behavior) and catching and logging errors with `break` statements to exit the loop.

Inside the try block, we first call `utils.encryption.receive` (a blocking function whose logic was already covered above) to wait for and then get the client's request data, which we assign to `data`. Then we check the value of the `authed` instance variable and dispatch the data to either `_handle_authentication` if it's falsy or `_handle_authenticated_commands` if it's truthy.

> ### The `_handle_authentication` method of the `RequestHandler` class
>
> The `_handle_authentication` method takes the `data` dictionary as an argument. It checks the value of the "command" key in the data and calls either `process_login` if the value is "login" or `process_register` if it's "register". If "command" is something else, it logs a warning.
>
>> ### The `process_login` method of the `RequestHandler` class
>>
>> The `process_login` method takes the `data` dictionary as an argument. It constructs a preliminary `login_result` dictionary with "type" of "login_result" and the "username" value from "data" (with empty string as default). It then calls the `validate` method of `user_manager` with the "username" and "password" values from `data` (empty defaults).
>> 
>>> #### The `validate` method of `UserManager`
>>>
>>> `validate` simply engages a lock and then checks if the username and password match a record in the `user_manager`'s loaded `users` dictionary. If they do, it returns `True`; otherwise, it returns `False`.
>>
>> If `validate` returns `True`, the `login_result` is updated with "response" set to "ok". It also sets `authed` to `True` and fetches the "username" attribute from `data` and assigns it to the `RequestHandler`'s `username` instance variable. Then it engages the `clients_lock` and adds the `username` to the `clients` dictionary of the RequestHandler class, with the value set to the `RequestHandler` instance. (This gives every currently authenicated user's RequestHandler instance access to the request API endpoint of the newly authenticated user's RequestHandler instance for the purpose of sending messages and notifications.) Finally, we call `_notify_peer_joined`, which engages the `clients_lock` and sends an event of "type" "peer_joined" to all other authenticated `clients`, with the "username" value from `self.username`.
>>
>> If, on the other hand, `validate` returns `False`, the `login_result` is updated with "response" set to "fail" and "reason" set to "Incorrect username or password!"
>>
>> Finally, the `login_result` is sent to the client using the `utils.encryption.send` method (explained above).
>>
>> ### The `process_register` method of the `RequestHandler` class
>>
>> The `process_register` method takes the `data` dictionary as an argument. It fetches the username and password from `data` and calls the `register` method of the `user_manager` with those values. If the `register` method returns `True`, it constructs a `register_result` dictionary with "type" set to "register_result" and "response" set to "ok". If `register` returns `False`, it constructs the dictionary with "response" set to "fail" and "reason" set to "Username already exists!". It also catches any error and sends a generic "fail" message to the client in this case.
>>
>>> #### The `register` method of `UserManager`

**TODO**

## Client `MainWindow` loop

**TODO**

The `show_main` method creates a `threading.Thread` instance to handle incoming messages from the server, and assigns it to the `receive_thread` instance variable. The `_receive_loop` method of the `NetworkManager` class is passed as the target for the thread, and the thread is started.