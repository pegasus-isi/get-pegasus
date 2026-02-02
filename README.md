# Python-based Pegasus Installer

This script installs Pegasus WMS and its dependencies (HTCondor) in a specified directory.

## Usage

To install Pegasus, run the script from within this directory:

```bash
./get_pegasus.py [--target <installation-directory>]
```

By default, Pegasus will be installed in `./pegasus-{version}`. You can specify a different location using the `--target` option.

After the installation is complete, you will need to source the environment file to configure your shell:

```bash
. <installation-directory>/env.sh
```

Then, you can start HTCondor:

```bash
condor_master
```

You can check the status of HTCondor with:

```bash
condor_status
condor_q
```

If HTCondor needs to be started at a later time, you can run `condor_master` again.

