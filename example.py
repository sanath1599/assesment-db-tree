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

def test_create_tag_and_restore(session: Session):
    tree = create_sample_tree(session)

    tag = "release-v1.0"
    tree.create_tag(session, tag=tag, description="First stable release")

    print("\nTree Versions after Tagging:")
    for version in tree.versions:
        print(f"Version {version.tag}: {version.description} - Created at {version.created_at}")

    restored_version = tree.restore_from_tag(session, tag="release-v1.0")
    print(f"\nRestored Version from Tag 'release-v1.0': {restored_version.tag}, {restored_version.description}")

def test_add_nodes_and_edges(session: Session):
    tree = create_sample_tree(session)

    second_version = tree.create_new_tree_version_from_tag(session, tag="v1.0")
    new_node = second_version.add_node(session, data={"setting": "new_value"})
    print(f"\nAdded new node with data: {new_node.data}")

    second_version.add_edge(session, node_id_1=1, node_id_2=new_node.id, data={"type": "new_dependency"})
    print(f"Added new edge between node 1 and node {new_node.id}")

def test_traversal(session: Session):
    tree = create_sample_tree(session)

    node1 = tree.get_latest_version(session).nodes[0]
    node2 = tree.get_latest_version(session).nodes[1]
    print("\nStarting Traversal from node 1:")
    
    def traverse_tree(node_id):
        node = session.get(TreeNode, node_id)
        print(f"Node {node.id}: {node.data}")
        stmt = select(TreeEdge).filter(TreeEdge.incoming_node_id == node.id)
        edges = session.exec(stmt).all()
        for edge in edges:
            print(f"Edge {edge.id}: {edge.data}")
            traverse_tree(edge.outgoing_node_id)

    traverse_tree(node1.id)

def test_find_path(session: Session):
    tree = create_sample_tree(session)

    node1 = tree.get_latest_version(session).nodes[0]
    node2 = tree.get_latest_version(session).nodes[1]
    node3 = tree.get_latest_version(session).add_node(session, data={"setting": "new_path_node"})

    tree.get_latest_version(session).add_edge(session, node_id_1=node2.id, node_id_2=node3.id, data={"type": "path_edge"})

    print("\nFinding path from node 1 to node 3:")
    
    def find_path(start_node_id, end_node_id):
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

    path = find_path(node1.id, node3.id)
    print(f"Path found: {path}")
    
    for node_id in path:
        node = session.get(TreeNode, node_id)
        print(f"Node {node.id}: {node.data}")

def main():
    init_db()
    with Session(engine) as session:
        test_create_tag_and_restore(session)
        test_add_nodes_and_edges(session)
        test_traversal(session)
        test_find_path(session)

if __name__ == "__main__":
    main()
