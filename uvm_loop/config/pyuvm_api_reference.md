# pyuvm 5.0.0 API reference (generated -- do not hand-edit)

Extracted from the pyuvm installed in the simulation worker by
`scripts/gen_pyuvm_api_reference.py`. These signatures are the real
ones. Use them as written; do not introspect the library at runtime.

Rules that cost the most to rediscover:

- **Logging.** There are no `uvm_info` / `uvm_warning` / `uvm_error`
  functions in this pyuvm. Use the component's own logger:
  `self.logger.info(msg)`, `.warning(msg)`, `.error(msg)`, `.critical(msg)`.
- **Phases.** `build_phase`, `connect_phase`, `end_of_elaboration_phase`,
  `start_of_simulation_phase`, `extract_phase`, `check_phase`,
  `report_phase` and `final_phase` are **plain `def`**. Only `run_phase` is
  `async def`. Declaring `run_phase` non-async, or any other phase async, is
  silently wrong -- the phase either never awaits or never runs.
- **Objections.** Raise and drop on the component, not on a phase object:
  `self.raise_objection()` / `self.drop_objection()` -- both plain calls, no
  argument required, no `phase` parameter. A `run_phase` that does not raise
  an objection can be cut short.
- **ConfigDB** is a singleton *instance*: `ConfigDB().set(...)`, with the
  parentheses. The separate `uvm_config_db` class is a SystemVerilog-style
  shim whose methods are **classmethods**: `uvm_config_db.set(...)`, with no
  parentheses, forwarding to the same store. Both spellings work and share
  data; `ConfigDB.set(...)` (class, no parens) does **not** -- it is an
  unbound method and raises. Pick one spelling and use it everywhere.
  Argument order is the same for both: `(context, inst_name, field_name,
  value)` for set, `(context, inst_name, field_name)` for get. `context` is a
  component or `None` (meaning uvm_root); `inst_name` is a path glob such as
  `"*"`.
- **Sequences.** `await seq.start(sequencer)`; inside `body`, use
  `await self.start_item(item)` ... `await self.finish_item(item)`. `body`,
  `start`, `start_item` and `finish_item` are all coroutines.
- **Drivers** get items with `await self.seq_item_port.get_next_item()` and
  must pair every one with `self.seq_item_port.item_done()`.
- **Constructors.** `uvm_component.__init__(self, name, parent)` -- both
  arguments are required for components. `uvm_object.__init__(self, name='')`
  takes a name only. Always forward them with `super().__init__(name, parent)`.

Do not shell out to read pyuvm's source to confirm any of the above.

Class surface (own methods only -- inherited ones live under the base):

### uvm_object — base: uvm_void
```python
def __init__(self, name='')
def clone(self)
def compare(self, rhs)
def convert2string(self)
def copy(self, rhs)
def create(name)
def do_compare(self, rhs)
def do_copy(self, rhs)
def get_default_logging_level()
def get_full_name(self)
def get_initial_logger_name(self)
def get_inst_id(self)
def get_name(self)
def get_report_verbosity(self)
def get_type_name(self)
def set_default_logging_level(default_logging_level)
def set_name(self, name)
def set_report_logger(self, logger)
def set_report_verbosity(self, verbosity)
```
Present but not implemented (never call): do_execute_op, do_pack, do_print, do_record, do_unpack, get_active_policy, get_object_type, get_type, get_uvm_seeding, pack, pack_bytes, pack_ints, pack_longints, pop_active_policy, print, push_active_policy, record, reseed, set_local, set_uvm_seeding, sprint, unpack, unpack_bytes, unpack_ints, unpack_longints

### uvm_transaction — base: uvm_object
```python
def __init__(self, name='', initiator=None)
def accept_tr(self, accept_time=0)
def begin_tr(self, begin_time=0, parent_handle=None) -> int
def do_accept_tr(self)   # User definable method to add to ``accept_tr()``
def do_begin_tr(self)   # User definable method
def end_tr(self, end_time=0, free_handle=True) -> None
def get_accept_time(self) -> int
def get_begin_time(self) -> int
def get_end_time(self) -> int
def get_initiator(self)
def get_transaction_id(self)
def set_id_info(self, other)
def set_initiator(self, initiator)
def set_transaction_id(self, txn_id)
```
Present but not implemented (never call): disable_recording, do_end_tr, enable_recording, get_event_pool, get_tr_handle, is_active, is_recording_enabled

### uvm_sequence_item — base: uvm_transaction
```python
def __init__(self, name)
def set_context(self, item)   # Use this to link a new response transaction to the request transaction
```

### uvm_component — base: uvm_report_object
```python
def __init__(self, name, parent=None)   # 13.1.2.1---This is new() in the IEEE-UVM, but we mean
def add_child(self, name, child)
def add_logging_handler_hier(self, handler)   # Add an additional handler all the way down the component hierarchy
def build_phase(self)
def cdb_get(self, label, inst_path='')   # A convenience routine that retrieves an object from
def cdb_set(self, label, value, inst_path='*')   # A convenience routing to store an object in the config_db using
def check_phase(self)
def clear_children(self)   # Removes the direct children from this component.
def clear_components()
def clear_hierarchy(self)   # Removes self from the UVM hierarchy
def connect_phase(self)
def create(name='', parent=None)
def disable_logging_hier(self)   # Disable logging for this component and all the way down the hierarchy
def drop_objection(self, description='')   # Drop an objection, usually at the end of the ``run_phase()``
def end_of_elaboration_phase(self)
def extract_phase(self)
def final_phase(self)
def get_child(self, name)   # 13.1.3.4
def get_children(self)   # 13.1.3.3
def get_depth(self)   # 13.1.3.8
def get_full_name(self)
def get_num_children(self)   # 13.1.3.5
def get_parent(self)
def has_child(self, name)   # 13.1.3.6
def lookup(self, name)   # 13.1.3.7
def objection(self)
def raise_objection(self, description='', stacklevel=1)   # Raise an objection, usually at the start of the ``run_phase()``
def remove_logging_handler_hier(self, handler)   # Remove a handler from all loggers below this component
def remove_streaming_handler_hier(self)   # Remove this component's streaming handler and all the way down
def report_phase(self)
async def run_phase(self)
def set_logging_level_hier(self, logging_level)   # Set the logging level for this component's logger
def start_of_simulation_phase(self)
```
Present but not implemented (never call): do_execute_op

### uvm_driver — base: uvm_component
```python
def __init__(self, name, parent)   # Creates and initializes an instance of this class using the normal
```

### uvm_monitor — base: uvm_component

### uvm_agent — base: uvm_component
```python
def active(self)
def build_phase(self)   # This ``build_phase()`` implements agent-specific behavior.
def get_is_active(self)   # Returns :data:`~uvm_active_passive_enum.UVM_ACTIVE` if the agent is
```

### uvm_scoreboard — base: uvm_component

### uvm_subscriber — base: uvm_component
```python
def __init__(self, name, parent)   # 13.1.2.1---This is new() in the IEEE-UVM, but we mean
def write(self, tt)   # Method that must be defined in each subclass. Access to this method by
```

### uvm_env — base: uvm_component

### uvm_test — base: uvm_component
```python
def __init__(self, name, parent=None)   # 13.1.2.1---This is new() in the IEEE-UVM, but we mean
def add_message_demotes(self, catcher)
def configure_uvm_reporting(self)
```

### uvm_root — base: uvm_component
```python
def __init__(self)   # 13.1.2.1---This is new() in the IEEE-UVM, but we mean
def clear_singletons(keep_set=None)   # Clear the singletons in the system.  This is used for testing
def find(self, comp_match: 'str') -> 'uvm_component | None'   # find does a find_all with comp = None and returns the first element in
def find_all(self, comp_match: 'str', comp: 'uvm_component | None' = None) -> 'list[uvm_component]'   # Returns a list of components matching a given comp_match string. Match
async def run_test(self, test_name, keep_singletons=False, keep_set=None)
```

### uvm_sequence — base: uvm_object
```python
def __init__(self, name='uvm_sequence')
async def body(self)   # This function gets launched in a thread when you run start()
async def finish_item(self, item)
async def get_response(self, transaction_id=None)
async def post_body(self)   # This function gets launced AFTER the function body() is started
async def pre_body(self)   # This function gets launced BEFORE the function body() is started
async def start(self, seqr=None, call_pre_post=True)   # Launch this sequence on the sequencer. Seqr cannot be None.
async def start_item(self, item)   # Sends an item to the sequencer and waits to be notified
```

### uvm_sequence_base — base: uvm_sequence_item

### uvm_sequencer — base: uvm_component
```python
def __init__(self, name, parent=None)   # 13.1.2.1---This is new() in the IEEE-UVM, but we mean
async def finish_item(self, item)
async def get_next_item(self)
async def get_response(self, txn_id=None)
async def put_req(self, req)
async def run_phase(self)
async def start_item(self, item)
```

### uvm_sequencer_base — base: uvm_object

### uvm_analysis_port — base: uvm_port_base
```python
def __init__(self, name, parent)   # 13.1.2.1---This is new() in the IEEE-UVM, but we mean
def connect(self, export)
def write(self, datum)   # Write to all connected analysis ports. This is a broadcast.
```

### uvm_analysis_export — base: uvm_export_base

### uvm_analysis_imp — base: uvm_port_base

### uvm_tlm_analysis_fifo — base: uvm_tlm_fifo
```python
def __init__(self, name, parent=None)   # uvm_tlm_fifo is a uvm_component
```

### uvm_tlm_fifo — base: uvm_tlm_fifo_base
```python
def __init__(self, name=None, parent=None, size=1)   # uvm_tlm_fifo is a uvm_component
def flush(self)   # Flush out the FIFO
def is_empty(self)   # Returns true if FIFO is empty
def is_full(self)   # Test for full FIFO
def size(self)
def used(self)
```

### ConfigDB
```python
def __init__(self)
def clear(self)   # Reset the ConfigDB. Used for testing.
def exists(self, context, inst_name, field_name)   # Returns true if there is data in the database at this location
def get(self, context, inst_name, field_name, default=<no-default>)   # The component path matches against the paths in the ConfigDB. The path
def set(self, context, inst_name, field_name, value)   # Stores an object in the db using the context and
def trace(self, method, context, inst_name, field_name, value)   # Output the ConfigDB activity if tracing is on.
async def wait_modified(self, context, inst_name, field_name)
```

### uvm_config_db
```python
def exists(cntxt: 'uvm_component | None', inst_name: 'str', field_name: 'str') -> 'bool'
def get(cntxt: 'uvm_component | None', inst_name: 'str', field_name: 'str', default: 'Any' = <no-default>) -> 'Any'
def set(cntxt: 'uvm_component | None', inst_name: 'str', field_name: 'str', value: 'Any') -> 'None'
async def wait_modified(cntxt: 'uvm_component | None', inst_name: 'str', field_name: 'str')
```

### ObjectionHandler
```python
def __init__(self)
def clear(self)
def drop_objection(self, dropper, description)
def get_objection_count(self)
def raise_objection(self, raiser, description, stacklevel=1)
async def run_phase_complete(self)
```

### uvm_factory
```python
def __init__(self)
def clear_all(self)   # Clear all the classes and overrides from the factory
def clear_overrides(self)   # Clear all the overrides from the factory
def create_component_by_name(self, requested_type_name, parent_inst_path='', name='', parent=None)   # Create a components using the name of the requested uvm_component type
def create_component_by_type(self, requested_type, parent_inst_path='', name='', parent=None)
def create_object_by_name(self, requested_type_name, parent_inst_path='', name='')
def create_object_by_type(self, requested_type, parent_inst_path='', name='')
def find_override_by_name(self, requested_type_name, full_inst_path)
def find_override_by_type(self, requested_type, full_inst_path)
def find_wrapper_by_name(self)
def is_type_name_registered(self, type_name)
def is_type_registered(self, uvm_type)
def print(self, debug_level=1)
def set_inst_alias(self, alias_type_name, original_type, full_inst_path)
def set_inst_override_by_name(self, original_type_name, override_type_name, full_inst_path)
def set_inst_override_by_type(self, original_type, override_type, full_inst_path)
def set_type_alias(self, alias_type_name, original_type)
def set_type_override_by_name(self, original_type_name, override_type_name, replace=True)
def set_type_override_by_type(self, original_type, override_type, replace=True)
```

