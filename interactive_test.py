from datetime import datetime
from sqlmodel import Session, create_engine, select
from models import Tree, TreeVersion, TreeNode, TreeEdge, init_db

sqlite_url = "sqlite:///kastle.db"
engine = create_engine(sqlite_url)

def create_sample_tree(session: Session):
    tree = Tree(name="Root Configuration")
    session.add(tree)
    session.commit()

    first_version = TreeVersion(tree_id=tree.id, tag="v1.0", description="Initial version")
    session.add(first_version)
    session.commit()

    node1 = first_version.add_node(session, data={"setting": "value1"})
    node2 = first_version.add_node(session, data={"setting": "value2"})

    first_version.add_edge(session, node_id_1=node1.id, node_id_2=node2.id, data={"type": "dependency"})

    return tree

def create_tag(session: Session, tree: Tree):
    tag = input("Enter the tag name (e.g., 'release-v1.0'): ")
    description = input("Enter a description for the tag: ")

    tree.create_tag(session, tag=tag, description=description)
    print(f"\nTag '{tag}' created successfully with description: {description}")

def restore_from_tag(session: Session, tree: Tree):
    tag = input("Enter the tag name to restore from: ")

    try:
        restored_version = tree.restore_from_tag(session, tag)
        print(f"\nRestored Version from Tag '{tag}': {restored_version.tag}, {restored_version.description}")
    except ValueError as e:
        print(e)

def add_node_and_edge(session: Session, tree: Tree):
    node_data = input("Enter node data (e.g., {'setting': 'new_value'}): ")
    try:
        node_data = eval(node_data) 
    except Exception as e:
        print(f"Invalid node data: {e}")
        return

    latest_version = tree.get_latest_version(session)
    new_node = latest_version.add_node(session, data=node_data)
    print(f"New node added: {new_node.data}")

    node1_id = int(input("Enter the ID of the first node for the edge: "))
    node2_id = int(input("Enter the ID of the second node for the edge: "))
    edge_data = input("Enter edge data (e.g., {'type': 'dependency'}): ")
    try:
        edge_data = eval(edge_data)  
    except Exception as e:
        print(f"Invalid edge data: {e}")
        return

    latest_version.add_edge(session, node_id_1=node1_id, node_id_2=node2_id, data=edge_data)
    print(f"Edge between node {node1_id} and node {node2_id} added with data: {edge_data}")

def traverse_tree(session: Session, tree: Tree):
    node_id = int(input("Enter the node ID to start traversal from: "))

    def traverse_tree_recursive(node_id):
        node = session.get(TreeNode, node_id)
        print(f"Node {node.id}: {node.data}")
        stmt = select(TreeEdge).filter(TreeEdge.incoming_node_id == node.id)
        edges = session.exec(stmt).all()  
        for edge in edges:
            print(f"Edge {edge.id}: {edge.data}")
            traverse_tree_recursive(edge.outgoing_node_id)

    print("\nStarting Traversal:")
    traverse_tree_recursive(node_id)

def find_path(session: Session, tree: Tree):
    start_node_id = int(input("Enter the starting node ID: "))
    end_node_id = int(input("Enter the ending node ID: "))

    def find_path_recursive(start_node_id, end_node_id):
        visited = set()
        path = []
        def dfs(node_id):
            if node_id in visited:
                return False
            visited.add(node_id)
            path.append(node_id)
            if node_id == end_node_id:
                return True
            stmt = select(TreeEdge).filter(TreeEdge.incoming_node_id == node_id)
            edges = session.exec(stmt).all()  
            for edge in edges:
                if dfs(edge.outgoing_node_id):
                    return True
            path.pop()
            return False
        
        dfs(start_node_id)
        return path

    path = find_path_recursive(start_node_id, end_node_id)
    print(f"\nPath found: {path}")
    
    for node_id in path:
        node = session.get(TreeNode, node_id)
        print(f"Node {node.id}: {node.data}")

def interactive_example():
    init_db()

    with Session(engine) as session:
        tree = create_sample_tree(session)

        while True:
            print("\n--- What would you like to do? ---")
            print("1. Create a tag")
            print("2. Restore from a tag")
            print("3. Add new nodes and edges to a tree version")
            print("4. Traverse the tree")
            print("5. Find a path between two nodes")
            print("6. Exit")
            
            choice = input("Enter the number of your choice: ")
            if choice == "1":
                create_tag(session, tree)
            elif choice == "2":
                restore_from_tag(session, tree)
            elif choice == "3":
                add_node_and_edge(session, tree)
            elif choice == "4":
                traverse_tree(session, tree)
            elif choice == "5":
                find_path(session, tree)
            elif choice == "6":
                print("Exiting the program.")
                break
            else:
                print("Invalid choice, please try again.")

def main():
    interactive_example()

if __name__ == "__main__":
    main()
