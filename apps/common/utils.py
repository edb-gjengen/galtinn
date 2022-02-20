from timeit import default_timer


def log_time(description):
    def __log_time(func):
        def __wrapper(*args, **kwargs):
            start = default_timer()
            print(description, end="", flush=True)

            ret = func(*args, **kwargs)

            end = default_timer()
            print(" {:.2f}s".format(end - start))
            return ret

        return __wrapper

    return __log_time
