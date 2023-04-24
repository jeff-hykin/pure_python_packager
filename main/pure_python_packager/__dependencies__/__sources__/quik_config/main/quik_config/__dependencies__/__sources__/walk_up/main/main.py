import os

def walk_up_until(file_to_find, start_path=None):
    here = start_path or os.getcwd()
    if not os.path.isabs(here):
        here = os.path.join(os.getcwd(), file_to_find)
    
    while 1:
        check_path = os.path.join(here, file_to_find)
        if os.path.exists(check_path):
            return check_path
        
        # reached the top
        if here == os.path.dirname(here):
            return None
        else:
            # go up a folder
            here = os.path.dirname(here)