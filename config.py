CONFIG = {
    "QUEUE": {
        "TASK_QUEUE": "https://www.hlidacstatu.cz/api/v2/internalq/Voice2TextGetTask",
        "REPORT_SUCCESS": "https://www.hlidacstatu.cz/api/v2/internalq/Voice2TextDone",
        "REPORT_FAILURE": "https://www.hlidacstatu.cz/api/v2/internalq/Voice2TextFailed/true",
        "HEADERS": {
            "Authorization": "xxx",
        }
    },
    "RUN": {
        "WAIT_SECONDS": 60,
        "LOCAL_FOLDER": "/var/ivysilani",
        "INPUT_FORMAT": ".mp3",
        "OUTPUT_FORMAT": ".ctm",
        "TEST_PHASE": False,
        "DEBUG_LEVEL": 0,
        "OVERWRITE": False,
    },
    "SFTP": {
        "USER_VARIABLE_NAME": "FTP_USER",
        "PWD_VARIABLE_NAME": "FTP_PWD",
        "URL": "dm3.devmasters.cz",
        "PORT": 990,
    }
}
