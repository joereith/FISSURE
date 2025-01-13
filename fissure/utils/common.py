from typing import Any, Dict, Optional, Tuple

#import distro
import logging
import logging.config
import os
import socket
import time
import yaml
import zmq
import zmq.asyncio
import zmq.auth
import zmq.auth.asyncio
import subprocess

FISSURE_ROOT: os.PathLike = os.path.abspath(os.path.join(__file__, "..", "..", ".."))
LOG_DIR: os.PathLike = os.path.join(FISSURE_ROOT, "Logs")
YAML_DIR: os.PathLike = os.path.join(FISSURE_ROOT, "YAML")
UI_DIR: os.PathLike = os.path.join(FISSURE_ROOT, "UI")
CERT_DIR: os.PathLike = os.path.join(FISSURE_ROOT, "certificates")
FLOW_GRAPH_LIBRARY_3_8: os.PathLike = os.path.join(FISSURE_ROOT, "Flow Graph Library", "maint-3.8")
FLOW_GRAPH_LIBRARY_3_10: os.PathLike = os.path.join(FISSURE_ROOT, "Flow Graph Library", "maint-3.10")
TOOLS_DIR: os.PathLike = os.path.join(FISSURE_ROOT, "Tools")
USER_CONFIGS_DIR: os.PathLike = os.path.join(FISSURE_ROOT, "YAML", "User Configs")
ARCHIVE_DIR: os.PathLike = os.path.join(FISSURE_ROOT, "Archive")
IQ_RECORDINGS_DIR: os.PathLike = os.path.join(FISSURE_ROOT, "IQ Recordings")
SENSOR_NODE_DIR: os.PathLike = os.path.join(FISSURE_ROOT, "fissure", "Sensor_Node")
GALLERY_DIR: os.PathLike = os.path.join(FISSURE_ROOT, "docs", "Gallery")
CLASSIFIER_DIR: os.PathLike = os.path.join(FISSURE_ROOT, "Classifier")
PLUGIN_DIR: os.PathLike = os.path.join(FISSURE_ROOT, "Plugins")


FISSURE_CONFIG_FILE = "fissure_config.yaml"
FISSURE_CONFIG_DEFAULT = os.path.join("User Configs", "default.yaml")
LOG_CONFIG_FILE = "logging.yaml"

OS_3_8_KEYWORDS = ["DragonOS Focal", "Ubuntu 20.04"]
OS_3_10_KEYWORDS = ["Ubuntu 22.04", "Kali", "DragonOS FocalX", "Raspberry Pi OS", "Parrot", "Ubuntu 24.04"]

QTERMINAL_LIST = ["DragonOS Focal", "DragonOS FocalX", "Kali"]
LXTERMINAL_LIST = ["Raspberry Pi OS"]
GNOME_TERMINAL_LIST = ["Ubuntu 20.04", "Ubuntu 22.04", "Parrot", "Ubuntu 24.04"]

DATABASE_TABLE_HEADERS = {
    "archive_collection": ["id", "name", "file_list", "filepath", "files", "format", "size", "notes", "parent_id", "created_at"],
    "archive_favorites": ["id", "file_name", "date", "format", "modulation", "notes", "protocol", "sample_rate", "samples", "size", "tuned_frequency"],
    "attack_categories": ["id", "category_name", "parent"],
    "attacks": ["id", "protocol", "attack_name", "modulation_type", "hardware", "attack_type", "filename", "category_name", "version"],
    "conditioner_flow_graphs": ["id", "isolation_category", "isolation_method", "hardware", "file_type", "data_type", "version", "parameter_names", "parameter_values", "parameter_labels", "filepath"],
    "demodulation_flow_graphs": ["id", "protocol", "modulation_type", "hardware", "filename", "output_type", "version"],
    "detector_flow_graphs": ["id", "detector_type", "hardware", "filename", "file_type", "version"],
    "inspection_flow_graphs": ["id", "hardware", "python_file", "version"],
    "modulation_types": ["id", "protocol", "modulation_type"],
    "packet_types": ["id", "protocol", "packet_name", "dissector", "fields", "sort_order"],
    "protocols": ["id", "protocol_name", "data_rates", "median_packet_lengths"],
    "soi_data": ["id", "protocol", "soi_name", "center_frequency", "start_frequency", "end_frequency", "bandwidth", "continuous", "modulation", "notes"],
    "triggers": ["id", "category", "trigger_name", "default_settings", "filename", "file_type", "version"]
}


class FissureUtilObjects:
    config: Dict = None
    zmq_ctx: zmq.asyncio.Context = None
    zmq_authenticator: zmq.auth.asyncio.AsyncioAuthenticator = None


__vars = FissureUtilObjects()


def init_logging():
    """
    Configure Logging
    """
    # Create the log directory if it doesn't already exist
    if not os.path.exists(LOG_DIR):  # pragma: no cover
        os.mkdir(LOG_DIR)

    # Read logging config file
    config = load_yaml(LOG_CONFIG_FILE)
    for handler in config["handlers"]:
        handler_info = config["handlers"][handler]
        if handler_info.get("filename") is not None:
            logfile = os.path.join(FISSURE_ROOT, handler_info.get("filename"))
            config["handlers"][handler]["filename"] = logfile

    # Set Logging Config
    logging.config.dictConfig(config)

    # print("After dictConfig:")
    # for name, logger in logging.Logger.manager.loggerDict.items():
    #     if isinstance(logger, logging.Logger):
    #         print(f"Logger: {name}, Handlers: {logger.handlers}, Propagate: {logger.propagate}")


def get_logger(source: str) -> logging.Logger:
    """
    Get the requested logger, initializing it if necessary

    :param source: logger source
    :type source: str
    :return: logger object
    :rtype: logging.Logger
    """

    # Format logger name if it's not the root fissure logger
    if source != "fissure":
        source = f"fissure.{source.lower()}"
    
    logger = logging.getLogger(source.lower())

    return logger


def update_logging_levels(logger, new_console_level=None, new_file_level=None):
    """
    Update the logging levels for a FISSURE component.
    """
    level_mapping = {
        "DEBUG": 10,
        "INFO": 20,
        "WARNING": 30,
        "ERROR": 40,
    }

    # # Print initial handler levels
    # for handler in logger.handlers:
    #     print(f"Handler {type(handler).__name__} level before update: {handler.level}")

    if new_console_level is not None and new_console_level.strip():
        console_level = level_mapping.get(new_console_level.upper(), 20)
        for handler in logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                handler.setLevel(console_level)
    else:
        console_level = logger.level

    if new_file_level is not None and new_file_level.strip():
        file_level = level_mapping.get(new_file_level.upper(), 20)
        for handler in logger.handlers:
            if isinstance(handler, logging.FileHandler):
                handler.setLevel(file_level)
    else:
        file_level = logger.level

    logger.setLevel(min(console_level, file_level))

    # # Print final handler levels
    # for handler in logger.handlers:
    #     print(f"Handler {type(handler).__name__} level after update: {handler.level}")
    # print(f"Logger level after update: {logger.level}")


def get_fg_library_dir(os_info: str) -> str:
    """
    Returns the maint-3.8 or maint-3.10 flow graph library directory.

    :param os_info: result of get_os_info()
    :type os_info: str
    :return: flow graph library directory filepath
    :rtype: str
    """
    # Choose Filepath Based on Operating System
    if any(keyword == os_info for keyword in OS_3_8_KEYWORDS):
        return FLOW_GRAPH_LIBRARY_3_8
    elif any(keyword == os_info for keyword in OS_3_10_KEYWORDS):
        return FLOW_GRAPH_LIBRARY_3_10
    else:
        return FLOW_GRAPH_LIBRARY_3_10
    

def get_plugin_fg_library_dir(os_info: str, basepath: str) -> str:
    """
    Returns the maint-3.8 or maint-3.10 flow graph library directory for a plugin.

    :param os_info: result of get_os_info()
    :type os_info: str
    :return: flow graph library directory filepath
    :rtype: str
    """
    # Choose Filepath Based on Operating System
    if any(keyword == os_info for keyword in OS_3_8_KEYWORDS):
        return os.path.join(basepath, "install_files", "Flow Graph Library", "maint-3.8")
    elif any(keyword == os_info for keyword in OS_3_10_KEYWORDS):
        return os.path.join(basepath, "install_files", "Flow Graph Library", "maint-3.10")
    else:
        return os.path.join(basepath, "install_files", "Flow Graph Library", "maint-3.10")


def get_default_expect_terminal(os_info: str) -> str:
    """
    Returns qterminal, lxterminal, or gnome-terminal based on operating system.

    :param os_info: result of get_os_info()
    :type os_info: str
    :return: terminal type
    :rtype: str
    """
    # Choose Default Terminal Based on Operating System
    if any(keyword == os_info for keyword in GNOME_TERMINAL_LIST):
        return "gnome-terminal"
    elif any(keyword == os_info for keyword in QTERMINAL_LIST):
        return "qterminal"
    elif any(keyword == os_info for keyword in LXTERMINAL_LIST):
        return "lxterminal"
    else:
        return "gnome-terminal"


def get_zmq_context() -> zmq.asyncio.Context:
    """
    :return: ZMQ Context
    :rtype: zmq.Context
    """
    if __vars.zmq_ctx is None:
        __vars.zmq_ctx = zmq.asyncio.Context()
    return __vars.zmq_ctx


def get_authenticator(allowed_keys: str = None) -> zmq.auth.asyncio.AsyncioAuthenticator:
    """
    :return: the ZMQ Authenticator
    :rtype: zmq.auth.asyncio.AsyncioAuthenticator
    """
    if __vars.zmq_authenticator is None:
        __vars.zmq_authenticator = zmq.auth.asyncio.AsyncioAuthenticator(context=__vars.zmq_ctx)
        __vars.zmq_authenticator.start()
        __vars.zmq_authenticator.allow()
        __vars.zmq_authenticator.configure_curve(domain=zmq.auth.CURVE_ALLOW_ANY, location=allowed_keys)
    return __vars.zmq_authenticator


def zmq_cleanup():  # pragma: no cover
    """
    Clean up ZMQ Context and stop the Authenticator
    """
    logger: logging.Logger = logging.getLogger("fissure")
    logger.debug("Cleaning Up ZMQ Context")
    if __vars.zmq_authenticator is not None:
        __vars.zmq_authenticator.stop()

        del __vars.zmq_authenticator
        __vars.zmq_authenticator = None

    if __vars.zmq_ctx is not None:
        # __vars.zmq_ctx.destroy(linger=0)

        del __vars.zmq_ctx
        __vars.zmq_ctx = None


def load_yaml(filename: str) -> Optional[Dict]:
    """
    Loads the settings from a YAML file and stores them in a dictionary

    :param filename: path to YAML file containing settings
    :type filename: str
    :return: dictionary representation of settings from the YAML file
    :rtype: Optional[Dict]
    """
    settings = None
    with open(os.path.join(YAML_DIR, filename), "r") as yaml_file:
        settings = yaml.load(yaml_file, yaml.FullLoader)
    return settings


def save_yaml(filename: str, data: Any):
    """
    Saves the settings to a YAML file

    :param filename: filename to dump settings to
    :type filename: str
    :param data: settings data to dump to file
    :type data: Any
    """
    logger: logging.Logger = logging.getLogger("fissure")
    stream = open(os.path.join(YAML_DIR, filename), "w")
    yaml.dump(data, stream)
    logger.debug(f"configuation file updated (YAML/{filename})")


def get_fissure_config() -> Dict:
    logger: logging.Logger = logging.getLogger("fissure")

    if __vars.config is None:
        __vars.config = load_yaml(FISSURE_CONFIG_FILE)
        remember = __vars.config.get("remember_configuration")
        if not remember:
            __vars.config = load_yaml(FISSURE_CONFIG_DEFAULT)
            logger.debug(f"loaded default config ({FISSURE_CONFIG_DEFAULT})")
        else:
            logger.debug(f"loaded fissure config ({FISSURE_CONFIG_FILE})")

    return __vars.config


def save_fissure_config(data: Dict):
    """
    If `remember_configuration` is set to `True`, store the configured settings,
    overwriting the `fissure_config.yaml` file.

    :param data: fissure configuration settings
    :type data: Dict
    """
    if data.get("remember_configuration") is True:
        save_yaml(FISSURE_CONFIG_FILE, data)


def get_timestamp(t: float = None) -> str:
    """
    :return: formatted UTC timestamp
    :rtype: str
    """
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t))


def get_ip_address() -> str:
    """
    :return: IP Address
    :rtype: str
    """
    hostname = socket.gethostname()
    return socket.gethostbyname(hostname)


def get_os_info() -> Tuple[str, str, str]:
    """
    :return: Linux Distribution Info (name, version, codename)
    :rtype: tuple
    """
    # return distro.linux_distribution()  # Potentially use this method once values are collected
    # ('Ubuntu', '20.04', 'focal')
    
    # This method contains previously gathered values
    # Detect Operating System

    # Ubuntu 24.04
    proc = subprocess.Popen("lsb_release -d 2>&1 | grep 'Ubuntu 24.04'", shell=True, stdout=subprocess.PIPE, )
    output = proc.communicate()[0].decode()
    if len(output) > 0:
        return "Ubuntu 24.04"
    
    # Ubuntu 22.04
    proc = subprocess.Popen("lsb_release -d 2>&1 | grep 'Ubuntu 22.04'", shell=True, stdout=subprocess.PIPE, )
    output = proc.communicate()[0].decode()
    if len(output) > 0:
        return "Ubuntu 22.04"
    
    # Ubuntu 20.04
    proc = subprocess.Popen("lsb_release -d 2>&1 | grep 'Ubuntu 20.04'", shell=True, stdout=subprocess.PIPE, )
    output = proc.communicate()[0].decode()
    if len(output) > 0:
        return "Ubuntu 20.04"
    
    # DragonOS Focal
    proc = subprocess.Popen("lsb_release -d 2>&1 | grep 'DragonOS Focal$'", shell=True, stdout=subprocess.PIPE, )
    output = proc.communicate()[0].decode()
    if len(output) > 0:
        return "DragonOS Focal"

    # DragonOS FocalX
    proc = subprocess.Popen("cat /etc/os-dragonos 2>&1 | grep 'DragonOS FocalX'", shell=True, stdout=subprocess.PIPE, )
    output = proc.communicate()[0].decode()
    if len(output) > 0:
        return "DragonOS FocalX"
    
    # Kali
    proc = subprocess.Popen("lsb_release -d 2>&1 | grep 'Kali'", shell=True, stdout=subprocess.PIPE, )
    output = proc.communicate()[0].decode()
    if len(output) > 0:
        return "Kali"
    
    # Raspberry Pi OS
    proc = subprocess.Popen("lsb_release -d 2>&1 | grep 'bookworm'", shell=True, stdout=subprocess.PIPE, )
    output = proc.communicate()[0].decode()
    if len(output) > 0:
        return "Raspberry Pi OS"
    
    # KDE Neon
    proc = subprocess.Popen("lsb_release -d 2>&1 | grep 'KDE Neon'", shell=True, stdout=subprocess.PIPE, )  # Test this
    output = proc.communicate()[0].decode()
    if len(output) > 0:
        return "Ubuntu 20.04"  # Same settings as Ubuntu 20.04
    
    # Parrot OS
    proc = subprocess.Popen("lsb_release -d 2>&1 | grep 'Parrot'", shell=True, stdout=subprocess.PIPE, )  # Parrot Security 6.1 (lorikeet)
    output = proc.communicate()[0].decode()
    if len(output) > 0:
        return "Parrot"
    
    # BackBox
    proc = subprocess.Popen("lsb_release -d 2>&1 | grep 'BackBox'", shell=True, stdout=subprocess.PIPE, )  # Test this
    output = proc.communicate()[0].decode()
    if len(output) > 0:
        return "Ubuntu 22.04"  # Same settings as Ubuntu 22.04


def isFloat(x):
    """
    Returns "True" if the input is a Float. Returns "False" otherwise.
    """
    # Check Value
    try:
        float(x)
    except ValueError:
        return False
    return True


def updateCRC(crc_poly, crc_acc, crc_input, crc_length):
    """
    Calculates CRC for bytes. Used in multiple tabs. Move this function somewhere else?
    """
    # 8-bit CRC
    if crc_length == 8:
        # Convert Hex Byte String to int
        crc_input_int = int(crc_input, 16)
        crc_acc_int = int(crc_acc, 16)
        crc_acc_int = crc_acc_int ^ crc_input_int
        for _ in range(8):
            crc_acc_int <<= 1
            if crc_acc_int & 0x0100:
                crc_acc_int ^= crc_poly
            # crc &= 0xFF

        # Convert to Hex String
        crc_acc = ("%0.2X" % crc_acc_int)[-2:]

    # 16-bit CRC
    elif crc_length == 16:
        # Convert Hex Byte String to int
        crc_input_int = int(crc_input, 16)
        crc_acc_int = int(crc_acc, 16)
        crc_acc_int = crc_acc_int ^ (crc_input_int << 8)
        for i in range(0, 8):
            if (crc_acc_int & 32768) == 32768:
                crc_acc_int = crc_acc_int << 1
                crc_acc_int = crc_acc_int ^ crc_poly
            else:
                crc_acc_int = crc_acc_int << 1

        # Convert to Hex String
        crc_acc = "%0.4X" % crc_acc_int

        # Keep Only the Last 2 Bytes
        crc_acc = crc_acc[-4:]

    # 32-bit CRC
    elif crc_length == 32:
        crc_input_int = int(crc_input, 16)
        crc_acc = crc_acc ^ crc_input_int
        for _ in range(0, 8):
            mask = -(crc_acc & 1)
            crc_acc = (crc_acc >> 1) ^ (crc_poly & mask)

    return crc_acc


def get_library_version():
    """
    Returns the library version for flow graphs and scripts stored in the database based on operating system.
    """
    # Return Value by Operating System
    os_info = get_os_info()
    if os_info in OS_3_8_KEYWORDS:
        return "maint-3.8"
    elif os_info in OS_3_10_KEYWORDS:
        return "maint-3.10"
