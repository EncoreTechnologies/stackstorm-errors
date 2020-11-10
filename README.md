[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

# Errors Pack

# Introduction
This pack holds all of the contains all actions and workflows needed for finding and formating
StackStorm errors

# Quick Start

**Steps**

1. Install the pack

    ``` shell
    st2 pack install https://github.com/EncoreTechnologies/stackstorm-errors.git
    ```

2. Execute an action (example: Build an execution tree)

    ``` shell
    st2 run errors.build_execution_tree st2_exe_id="testID"
    ```

# Usage

## Actions

| Action | Description |
|--------|-------------|
| build_execution_tree | Builds an execution tree of the given task |
| get_formatted_error | Finds an error in the given task and formats the result into an HTML tagged output |

### Action Example - errors.build_execution_tree

`errors.build_execution_tree` builds an execution tree of a given StackStorm task:

```shell
st2 run errors.build_execution_tree st2_exe_id="5fa45525935a74a08162cd7b"
```

Workflow usage:

```yaml
get_error_execution_tree:
  action: errors.build_execution_tree
  input:
    st2_exe_id: 5fa45525935a74a08162cd7b
```

### Action Example - errors.get_formatted_error

`errors.get_formatted_error` Finds an error in the given task and formats the result into an HTML tagged output

```shell
st2 run errors.get_formatted_error st2_exe_id="5fa45525935a74a08162cd7b"
```

Workflow usage:

```yaml
get_error:
  action: errors.get_formatted_error
  input:
    st2_exe_id: "5fa45525935a74a08162cd7b"
```
