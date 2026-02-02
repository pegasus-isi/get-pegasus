# Pegasus Installer

## Project Overview

This project contains a Python script (`get-pegasus-py/get_pegasus.py`) that automates the installation of Pegasus Workflow Management System (WMS) and its primary dependency, HTCondor. The script is designed to be run on Linux and macOS systems.

The script performs the following actions:

1.  **System Detection:** Identifies the user's operating system, distribution, version, and architecture.
2.  **Downloads:** Fetches the correct binary tarballs for HTCondor and Pegasus WMS from their official distribution sites.
3.  **Installation:** Extracts the downloaded tarballs into a user-specified directory (defaults to `./pegasus-{version}`).
4.  **Configuration:**
    *   Generates a configuration file for HTCondor (`condor.conf`).
    *   Initializes HTCondor security by creating the necessary tokens.
    *   Creates an `env.sh` script to easily configure the user's shell environment for using Pegasus and HTCondor.

## Building and Running

This project is a standalone Python script and does not require a separate build process.

### Running the Installer

To run the Pegasus installer, execute the following command from the project root directory:

```bash
python3 get-pegasus-py/get_pegasus.py [--target <installation-directory>]
```

*   By default, the software will be installed in a `pegasus-{version}` directory in the current working directory.
*   You can specify a different installation path using the optional `--target` argument. For example:

```bash
python3 get-pegasus-py/get_pegasus.py --target ./my-pegasus-install
```

### Post-Installation

After the script finishes, you need to source the generated environment file to use Pegasus and HTCondor:

```bash
. <installation-directory>/env.sh
```

Once the environment is configured, you can start the HTCondor service:

```bash
condor_master
```

You can then verify that HTCondor is running with:

```bash
condor_status
condor_q
```

## Development Conventions

*   The script is written in Python 3 and should be Python 3.6 compatible.
*   Do not add any Python 3 modules except basic ones found in most standard Python 3 installs. The script should be portable.
*   It follows a procedural programming style with clear functions for each major step of the installation process.
*   Logging is used to provide informative output to the user during the installation.
*   The script includes error handling to clean up the installation directory if any step fails.

## Testing

To run the tests, execute the following command from the project's root directory:

```bash
python3 -m unittest get-pegasus-py/test_get_pegasus.py
```
