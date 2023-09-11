def parse(func, fallback=None): 
    try: 
        return func()
    except Exception: 
        return fallback 
