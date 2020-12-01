[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

# Errors Pack

# Introduction
This pack contains all actions and workflows needed for finding and formating
StackStorm errors. The errors and execution tree are obtained by using
the st2 api (python module). Workflows with their own custom errors are found
first and if there are none we just return the errors from the child-most
execution

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
| get_error_data | Workflow used to find the error and execution tree of a given execution

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
    st2_exe_id: "5fa45525935a74a08162cd7b"
```

Example output:

```
  - name: +> encore.provision
    status: running
  - name: <pre><code>      dispatch</pre></code>
    status: succeeded
  - name: <pre><code>   +> preprovision</pre></code>
    status: failed
  - name: <pre><code>         template_get_info</pre></code>
    status: succeeded
  - name: <pre><code>         build_description</pre></code>
    status: succeeded
  - name: <pre><code>         os_version_parse</pre></code>
    status: succeeded
  - name: <pre><code>         get_network_info</pre></code>
    status: succeeded
  - name: <pre><code>         build_dns_records</pre></code>
    status: succeeded
  - name: <pre><code>         ad_dispatch</pre></code>
    status: succeeded
  - name: <pre><code>      +> external_systems_check_fqdn</pre></code>
    status: failed
  - name: <pre><code>            validate_vsphere_name_unique</pre></code>
    status: succeeded
```

### Action Example - errors.get_formatted_error

`errors.get_formatted_error` Finds an error in the given task and formats the result into an HTML tagged output as well as hard returns

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
Example output (HTML):

```
Error task: external_systems_check_fqdn<br>Error execution ID: 5fb5746e295becef56bf2195<br>Error message: VM with the name=test.example.com already exists in vSphere<br>
```

Example output (hard returns):

```
Error task: external_systems_check_fqdn
Error execution ID: 5fb5746e295becef56bf2195
Error message: VM with the name=test.example.com already exists in vSphere
```

Custom Error Messages:

Workflows with their own custom errors, in StackStorm's output, are found
first and if there are none we just return the errors from the child-most
execution

Example:
(https://github.com/StackStorm-Exchange/stackstorm-menandmice/blob/master/actions/workflows/test_hostname.yaml)

```python
parent_errors = execution_result['output']['error']
```

Example output (hard returns):

```
result:
    Error task: external_systems_check
    Error execution ID: 5fbc1d8db05eda3452d85013
    Error message: VM still exists in vsphere with name=test.example.com
    Hostname=test is already in use in menandmice
    VM still exists in puppet with name=test.example.com
```



