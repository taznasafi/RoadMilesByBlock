from arcpy import ExecuteError, GetMessages
import logging


def timer(starttime, endtime, state=None):
    hours, rem = divmod(endtime - starttime, 3600)
    minutes, seconds = divmod(rem, 60)
    if state:
        print("\n**** end of the state {} task ****\n".format(state))
    print("{:0>2}:{:0>2}:{:05.2f}".format(int(hours), int(minutes), seconds))

def create_error_logger():
    """
    Creates a logging object and returns it
    """
    logger = logging.getLogger("*** arcpy_Error_Logger ***")
    logger.setLevel(logging.INFO)

    # create the logging file handler
    fh = logging.FileHandler(r"./error_logger.log")

    fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(fmt)
    fh.setFormatter(formatter)

    # add handler to logger object
    logger.addHandler(fh)

    return logger

def create_logger():
    """
    Creates a logging object and returns it
    """
    logger = logging.getLogger("*** arcpy_EVENT_Logger ***")
    logger.setLevel(logging.INFO)

    # create the logging file handler
    fh = logging.FileHandler(r"./logger.log")

    fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(fmt)
    fh.setFormatter(formatter)

    # add handler to logger object
    logger.addHandler(fh)
    return logger


def event_logger(log):

    '''
        A decorator that wraps the passed in function and logs
    arcpy events

    @param logger: The logging object
    '''

    def decorator(func):

        def wrapper(*args, **kwargs):
            msgs = "\n***********{}*****************\n".format(func.__name__)
            msgs += GetMessages()
            log.info(msgs)
            return func(*args, **kwargs)
        return wrapper

    return decorator



def arcpy_exception(log):

    """
    A decorator that wraps the passed in function and logs
    exceptions should one occur

    @param log: The logging object
    """


    def decorator(func):

        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ExecuteError:

                msgs = "\n************* \n{}\n************* \n".format(GetMessages(2))

                msgs+=func.__name__

                print(msgs)

                log.exception(msgs)

        return wrapper
    return decorator





