class DebugColor:
    RED = 31
    GREEN = 32
    YELLOW = 33
    BLUE = 34
    MAGENTA = 35
    CYAN = 36

def cprint(text: str, color: int) -> None:
    print(f"\033[{color}m{text}\033[0m")
    
def cprint(text: str, color: DebugColor) -> None:
    print(f"\033[{color}m{text}\033[0m")