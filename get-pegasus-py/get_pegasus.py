#!/usr/bin/env python3

import argparse
import logging
import os
import platform
import shutil
import socket
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path
from urllib.request import urlretrieve


pegasus_version = "5.1.2-dev.0"
htcondor_version = "25.x"

logging.basicConfig(level=logging.INFO, format="%(message)s")

def install_pegasus(target_dir: Path, arch: str, os_name: str, os_version: str):
    base_url = f"https://download.pegasus.isi.edu/pegasus/{pegasus_version}"
    
    if os_name == "debian":
        p_os_name = "deb"
    else:
        p_os_name = os_name

    tarball_name = f"pegasus-binary-{pegasus_version}-{arch}_{p_os_name}_{os_version}.tar.gz"
    tarball_path = target_dir / tarball_name

    logging.info(f"Downloading Pegasus tarball: {tarball_name}")
    urlretrieve(f"{base_url}/{tarball_name}", tarball_path)

    with tarfile.open(tarball_path, "r:gz") as tar:
        if sys.version_info >= (3, 9):
            tar.extractall(path=target_dir, filter="tar")
        else:
            tar.extractall(path=target_dir)

    tarball_path.unlink()

    pegasus_dir = next(target_dir.glob("pegasus-*"))
    pegasus_dir.rename(target_dir / "pegasus")



def install_htcondor(target_dir: Path, arch: str, os_name: str, os_version: str):
    base_url = f"https://htcss-downloads.chtc.wisc.edu/tarball/{htcondor_version}/current"
    
    c_os_name = ""
    c_os_version = os_version

    if os_name == "debian":
        c_os_name = "Debian"
    elif os_name == "rhel":
        c_os_name = "AlmaLinux"
    elif os_name == "suse":
        c_os_name = "AlmaLinux"
    elif os_name == "macos":
        c_os_name = "macOS"
        c_os_version = ""
    else:
        raise ValueError(f"Unable to determine HTCondor tarball for {os_name}")

    tarball_name = f"condor-{arch}_{c_os_name}{c_os_version}-stripped.tar.gz"
    tarball_path = target_dir / tarball_name
    
    logging.info(f"Downloading HTCondor tarball: {tarball_name}")
    urlretrieve(f"{base_url}/{tarball_name}", tarball_path)

    with tarfile.open(tarball_path, "r:gz") as tar:
        if sys.version_info >= (3, 9):
            tar.extractall(path=target_dir, filter="tar")
        else:
            tar.extractall(path=target_dir)

    tarball_path.unlink()
    
    condor_dir = next(target_dir.glob("condor-*"))
    condor_dir.rename(target_dir / "condor")


def env_setup(target_dir: Path):
    env_sh_path = target_dir / "env.sh"
    with env_sh_path.open("w") as f:
        f.write(
            f"""
export PATH={target_dir}/pegasus/bin:{target_dir}/condor/bin:{target_dir}/condor/sbin:$PATH
export CONDOR_CONFIG={target_dir}/condor/condor.conf
"""
        )
    
    # Instead of sourcing, we can just set the environment for the configure step
    path = os.environ.get("PATH", "")
    new_path = ":".join([
        str(target_dir / "pegasus/bin"),
        str(target_dir / "condor/bin"),
        str(target_dir / "condor/sbin"),
        path
    ])
    os.environ["PATH"] = new_path
    os.environ["CONDOR_CONFIG"] = str(target_dir / "condor/condor.conf")


def configure(target_dir: Path, os_name: str):
    condor_config_path = target_dir / "condor" / "condor.conf"
    with condor_config_path.open("w") as f:
        f.write(
            f"""
RELEASE_DIR = {target_dir}/condor
LOCAL_DIR = $(RELEASE_DIR)/local
REQUIRE_LOCAL_CONFIG_FILE = false
RUN     = $(LOCAL_DIR)/run
LOG     = $(LOCAL_DIR)/log
LOCK    = $(LOCAL_DIR)/lock
SPOOL   = $(LOCAL_DIR)/spool
EXECUTE = $(LOCAL_DIR)/execute
BIN     = $(RELEASE_DIR)/bin
LIB     = $(RELEASE_DIR)/lib64/condor
INCLUDE = $(RELEASE_DIR)/include/condor
SBIN    = $(RELEASE_DIR)/sbin
LIBEXEC = $(RELEASE_DIR)/libexec
SHARE   = $(RELEASE_DIR)/usr/share/condor

PROCD_ADDRESS = $(RUN)/procd_pipe

DAEMON_LIST = MASTER, COLLECTOR, SCHEDD, NEGOTIATOR, STARTD

CONDOR_HOST = localhost

USE_SHARED_PORT = False
COLLECTOR_PORT = {10000 + os.urandom(2)[0] % 40000}
COLLECTOR_USES_SHARED_PORT = False

# idtokens - good base for pilots
SEC_PASSWORD_DIRECTORY = $(RELEASE_DIR)/etc/passwords.d
SEC_TOKEN_SYSTEM_DIRECTORY = $(RELEASE_DIR)/etc/tokens.d
SEC_TOKEN_DIRECTORY = $(SEC_TOKEN_SYSTEM_DIRECTORY)

SEC_DEFAULT_AUTHENTICATION = REQUIRED
SEC_DEFAULT_ENCRYPTION = REQUIRED
SEC_DEFAULT_INTEGRITY = REQUIRED
SEC_DEFAULT_AUTHENTICATION_METHODS = FS, IDTOKEN
SEC_CLIENT_AUTHENTICATION_METHODS = $(SEC_DEFAULT_AUTHENTICATION_METHODS)
# With strong security, do not use IP based controls
ALLOW_WRITE = *
ALLOW_READ = *
ALLOW_ADMINISTRATOR = {os.getlogin()}@{socket.getfqdn()}

# dynamic slots
SLOT_TYPE_1 = cpus=100%,disk=100%,swap=100%
SLOT_TYPE_1_PARTITIONABLE = TRUE
NUM_SLOTS = 1
NUM_SLOTS_TYPE_1 = 1
"""
        )

    dirs_to_create = [
        "run",
        "log",
        "lock",
        "spool",
        "execute"
    ]
    for dir_var in dirs_to_create:
        dir_path = target_dir / "condor" / "local" / dir_var
        if not Path(dir_path).exists():
                Path(dir_path).mkdir(parents=True)

    dirs_to_create = [
        "tokens.d",
        "passwords.d",
    ]
    for dir_var in dirs_to_create:
        dir_path = target_dir / "condor" / "etc" / dir_var
        if not Path(dir_path).exists():
                Path(dir_path).mkdir(parents=True)

    pool_password_path = target_dir / "condor/etc/passwords.d/POOL"
    with open(pool_password_path, "wb") as f:
        f.write(os.urandom(128))
    pool_password_path.chmod(0o600)

    personal_token_path = target_dir / "condor/etc/tokens.d/personal.token"
    user_at_host = f"{os.getlogin()}@{socket.getfqdn()}"
    
    # Need to make sure condor bins are on the path and CONDOR_CONFIG is set
    os.environ["PATH"] = str(target_dir / "condor/bin") + ":" + os.environ["PATH"]
    os.environ["CONDOR_CONFIG"] = str(condor_config_path)
    
    # Create token
    with personal_token_path.open("w") as f:
        subprocess.run(
            [
                "condor_token_create",
                "-key",
                "POOL",
                "-identity",
                user_at_host,
            ],
            stdout=f,
            check=True,
        )
    personal_token_path.chmod(0o600)

    if os_name != "macos":
        subprocess.run(
            [str(target_dir / "pegasus/bin/pegasus-configure-glite")],
            stdout=subprocess.DEVNULL,
            check=True,
        )


def success_message(target_dir: Path):
    logging.info(
        f"""
Thank you for exploring Pegasus WMS. Your environment is now installed.
To get it configured, please source:

    . {target_dir}/env.sh

Then start HTCondor with:

    condor_master

You should then be able to execute HTCondor command such as:

    condor_status
    condor_q

You are then ready to submit your first workflow!
"""
    )


def get_system():
    arch = platform.machine()
    os_name = platform.system()
    os_version = platform.release()

    if os_name == "Linux":
        try:
            with open("/etc/os-release", "r") as f:
                os_release_info = {}
                for line in f:
                    line = line.strip()
                    if "=" in line:
                        key, value = line.split("=", 1)
                        os_release_info[key] = value.strip('"')
            os_name = os_release_info["ID"]
            os_version = os_release_info["VERSION_ID"]
        except FileNotFoundError:
            # if /etc/os-release is not available, we can't determine the distro
            raise OSError("Unable to determine Linux distribution")

        os_map = {
            "debian": "debian",
            "ubuntu": "debian",
            "centos": "rhel",
            "rocky": "rhel",
            "scientific": "rhel",
            "almalinux": "rhel",
            "fedora": "fedora",
            "sles": "suse",
            "opensuse-leap": "suse",
            "opensuse-tumbleweed": "suse",
        }
        os_name = os_map.get(os_name, os_name)

        os_version = os_version.split(".")[0]

    elif os_name == "Darwin":
        os_name = "macos"
        os_version = platform.mac_ver()[0].split(".")[0]

    else:
        raise OSError("Unsupported operating system")

    if not all([os_name, os_version, arch]) or "UNKNOWN" in [
        os_name,
        os_version,
        arch,
    ]:
        raise OSError("Failed to get system info")

    return arch, os_name, os_version


def main():
    parser = argparse.ArgumentParser(description="Install Pegasus WMS.")
    parser.add_argument(
        "--target",
        type=Path,
        default=Path.cwd() / f"pegasus-{pegasus_version}",
        help="Target directory for installation",
    )
    args = parser.parse_args()

    target_dir = args.target.resolve()

    if target_dir.exists():
        logging.error(f"ERROR: target directory ({target_dir}) exists. Unable to continue")
        exit(1)

    logging.info(f"Will install into {target_dir}")
    target_dir.mkdir(parents=True)

    try:
        arch, os_name, os_version = get_system()
        logging.info(f"Arch: {arch}    Base OS: {os_name}    OS Version: {os_version}")

        install_pegasus(target_dir, arch, os_name, os_version)
        install_htcondor(target_dir, arch, os_name, os_version)
        env_setup(target_dir)
        configure(target_dir, os_name)
        success_message(target_dir)
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        exit(1)

if __name__ == "__main__":
    main()