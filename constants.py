# constants.py

# Default UNC path to users folder on remote / source
USER_PROFILE_SUBPATH = r"C$\Users"

ROBOCOPY_PROFILE_SUBPATH = "C$\\Users"

# Common RoboCopy options (robust + multithreaded + restartable + logging-friendly)
ROBOCOPY_OPTIONS = [
    "/S",  # Copy subdirectories, not including empty ones
    "/Z",  # Restartable mode (useful for flaky networks)
    "/MT:8",  # Multi-threaded copy (8 threads — adjust based on environment)
    "/R:3",  # Retry 3 times on failed copies
    "/W:5",  # Wait 5 seconds between retries
    "/NFL",  # No file list (speeds up logging)
    "/NDL",  # No directory list
    "/NP",  # No progress shown in output
]

# Files known to be machine-specific, unneeded, or locked (registry hives, temp system files)
ROBOCOPY_EXCLUDE_FILES = [
    "NTUSER.DAT",
    "ntuser.dat.LOG1",
    "ntuser.dat.LOG2",
    "UsrClass.dat",
    "UsrClass.dat.LOG1",
    "UsrClass.dat.LOG2",
]

# Subfolders within included folders (e.g., Chrome) that should be skipped due to size or irrelevance
ROBOCOPY_EXCLUDE_DIRS = [
    "Default\\Cache",
    "Default\\Code Cache",
]

# Folders under AppData\Local worth migrating to preserve user data and settings
APPDATA_LOCAL_INCLUDE_DIRS = [
    "AppData\\Local\\Google\\Chrome\\User Data\\Default",
    "AppData\\Local\\Mozilla",
    "AppData\\Local\\MarchNetworks",
    "AppData\\Local\\OpenILS",
    "AppData\\Local\\Hatch",
    "AppData\\Local\\Honeywell",
]

# Roaming profiles - generally smaller and more configuration/history-oriented
APPDATA_ROAMING_INCLUDE_DIRS = [
    "AppData\\Roaming\\Mozilla",
    "AppData\\Roaming\\OpenILS",
    "AppData\\Roaming\\Microsoft\\Windows\\Recent",  # Recent items (shortcuts)
    "AppData\\Roaming\\Microsoft\\Windows\\Recent\\AutomaticDestinations",  # Jump lists (auto)
    "AppData\\Roaming\\Microsoft\\Windows\\Recent\\CustomDestinations",  # Jump lists (custom)
]
