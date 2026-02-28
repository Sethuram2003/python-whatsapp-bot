from mcp.server.fastmcp import FastMCP
import os
from neo4j import GraphDatabase, basic_auth
from dotenv import load_dotenv

load_dotenv()

mcp = FastMCP("PipeStatus")

neo4j_service = None

class Neo4jDBManager:
    def __init__(self, uri, admin_user, admin_password, db_name):
        """
        Initialize the Neo4jDBManager with admin credentials.
        """
        self.uri = uri
        self.admin_user = admin_user
        self.admin_password = admin_password
        self.driver = GraphDatabase.driver(
            self.uri, auth=basic_auth(self.admin_user, self.admin_password), database=db_name
        )

    def relationship_exists(self, from_node: str, to_node: str) -> bool:
        """
        Check if a relationship exists between two nodes, in either direction.
        Returns True if a connection exists, False otherwise.
        """
        with self.driver.session() as session:
            try:
                query = """
                MATCH (a:Location)-[r:CONNECTED_TO]-(b:Location)
                WHERE (a.name = $from_node AND b.name = $to_node) 
                OR (a.name = $to_node AND b.name = $from_node)
                RETURN r
                """
                result = session.run(
                    query,
                    from_node=from_node,
                    to_node=to_node
                )
                record = result.single()
                if record:
                    print(f"Relationship exists between {from_node} and {to_node}")
                    return True
                else:
                    print(f"No relationship exists between {from_node} and {to_node}")
                    return False
            except Exception as e:
                print(f"Error checking relationship: {e}")
                return False

    def get_attached_nodes(self, node_name: str) -> list:
        """
        Find all nodes directly connected (attached) to the given node.
        Returns a list of neighbor node names.
        """
        with self.driver.session() as session:
            try:
                query = """
                MATCH (n:Location {name: $node_name})-[r:CONNECTED_TO]-(neighbor:Location)
                RETURN neighbor.name AS neighbor_name
                """
                result = session.run(query, node_name=node_name)
                neighbors = [record["neighbor_name"] for record in result]
                print(f"Nodes attached to {node_name}: {neighbors}")
                return neighbors
            except Exception as e:
                print(f"Error fetching attached nodes for {node_name}: {e}")
                return []

    def get_node_distance_and_angle(self, from_node: str, to_node: str) -> dict:
        """
        Retrieve the distance and angle properties of the relationship between two nodes.
        The relationship can exist in either direction.
        Returns a dictionary with keys 'distance' and 'angle' if found, otherwise None.
        """
        with self.driver.session() as session:
            try:
                query = """
                MATCH (a:Location {name: $from_node})-[r:CONNECTED_TO]-(b:Location {name: $to_node})
                RETURN r.distance AS distance, r.angle AS angle
                """
                result = session.run(query, from_node=from_node, to_node=to_node)
                record = result.single()
                if record:
                    distance = record["distance"]
                    angle = record["angle"]
                    print(f"Distance between {from_node} and {to_node}: {distance}, Angle: {angle}")
                    return {"distance": distance, "angle": angle}
                else:
                    print(f"No relationship found between {from_node} and {to_node}")
                    return None
            except Exception as e:
                print(f"Error fetching distance and angle between {from_node} and {to_node}: {e}")
                return None

    def close(self):
        """
        Close the driver connection.
        """
        self.driver.close()


def get_neo4j_service() -> Neo4jDBManager:
    """FastAPI dependency to get Neo4j service instance"""
    global neo4j_service

    if neo4j_service is None:
        neo4j_service = Neo4jDBManager(
            uri = os.getenv("NEO4J_URI", "neo4j://localhost:7687"),
            admin_user = os.getenv("NEO4J_USERNAME", "neo4j"),
            admin_password = os.getenv("NEO4J_PASSWORD", "password"),
            db_name=os.getenv("NEO4J_DATABASE")
        )
    return neo4j_service

def close_neo4j_service():
    """Close Neo4j service connection"""
    global neo4j_service
    
    neo4j_service.close()

    
@mcp.tool()
async def get_nearby_pipes(
    pipe:str
) -> str:
    """
    Get all pipes directly connected to the given pipe.
    Args:
    pipe (str): Name of the pipe to find neighbors for
    Returns:
    str: A message listing all nearby pipes, or an error message if the check fails.
    """
    try:
        service = get_neo4j_service()
        neighbors = service.get_attached_nodes(pipe)
        if neighbors:
            return f"✅ Pipes directly connected to {pipe}: {', '.join(neighbors)}"
        else:
            return f"❌ No pipes are directly connected to {pipe}"
        
    except Exception as e:
        return f"❌ Failed to get nearby pipes: {str(e)}"
    

@mcp.tool()
async def get_distance_and_angle_between_pipes(
    pipe_1: str,
    pipe_2: str
) -> str:
    """
    Get the distance and angle from pipe1 to pipe2 if a connection exists.
    Args:
        pipe_1 (str): Name of the first pipe
        pipe_2 (str): Name of the second pipe
    Returns:
        str: A message with the distance and angle, or an error message if the check fails.
    """
    try:
        service = get_neo4j_service()
        if service.relationship_exists(pipe_1, pipe_2):
            
            data = service.get_node_distance_and_angle(pipe_1, pipe_2)

            return f"✅ Distance from {pipe_1} to {pipe_2}: {data['distance']}m, Angle: {data['angle']}°"
        else:
            return f"❌ No connection exists between {pipe_1} and {pipe_2}"
    except Exception as e:
        return f"❌ Failed to get distance and angle: {str(e)}"
    

if __name__ == "__main__":
    print("Starting PipeStatus MCP Server...")
    mcp.run()
