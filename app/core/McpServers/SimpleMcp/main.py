from mcp.server.fastmcp import FastMCP
import datetime
import random

mcp = FastMCP("BasicUtilityServer")

@mcp.tool()
async def add_numbers(a: int, b: int) -> int:
    """
    Adds two numbers.
    """
    return a + b

@mcp.tool()
async def get_current_time() -> str:
    """
    Returns current date and time.
    """
    return str(datetime.datetime.now())

@mcp.tool()
async def random_number(min_value: int, max_value: int) -> int:
    """
    Returns a random number between min_value and max_value.
    """
    return random.randint(min_value, max_value)


if __name__ == "__main__":
    print("Starting BasicUtilityServer MCP...")
    mcp.run()