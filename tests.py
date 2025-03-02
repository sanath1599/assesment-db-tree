import pytest
from sqlmodel import Session, create_engine, SQLModel, select  
from models import Tree, TreeVersion, TreeNode, TreeEdge, init_db


test_engine = create_engine("sqlite:///kastle.db")

@pytest.fixture(scope="function")
def session():
    """Fixture to create a fresh database session for each test."""
    SQLModel.metadata.create_all(test_engine)
    with Session(test_engine) as session:
        yield session
    SQLModel.metadata.drop_all(test_engine)

def run_test(test_name, test_func, session):
    try:
        test_func(session)
        print(f"Test '{test_name}' PASSED.")
    except Exception as e:
        print(f"Test '{test_name}' FAILED: {e}")

#  Test for creating a tree and version
def test_create_tree_and_version(session):
    tree = Tree(name="Test Tree")
    session.add(tree)
    session.commit()
    assert tree.id is not None

    version = TreeVersion(tree_id=tree.id, tag="v1.0", description="Initial version")
    session.add(version)
    session.commit()

    retrieved_version = session.get(TreeVersion, version.id)
    assert retrieved_version is not None
    assert retrieved_version.tag == "v1.0"

#  Test for creating multiple versions
def test_create_multiple_versions(session):
    tree = Tree(name="Test Tree for Multiple Versions")
    session.add(tree)
    session.commit()

    version1 = TreeVersion(tree_id=tree.id, tag="v1.0", description="Initial version")
    version2 = TreeVersion(tree_id=tree.id, tag="v1.1", description="Updated version")
    session.add(version1)
    session.add(version2)
    session.commit()

    versions = session.exec(select(TreeVersion).filter(TreeVersion.tree_id == tree.id)).all()  # Using session.exec()
    assert len(versions) == 2
    assert versions[0].tag == "v1.0"
    assert versions[1].tag == "v1.1"

#  Test for adding nodes and edges
def test_add_nodes_and_edges(session):
    tree = Tree(name="Node Edge Test Tree")
    session.add(tree)
    session.commit()

    version = TreeVersion(tree_id=tree.id, tag="v1.0", description="Testing nodes and edges")
    session.add(version)
    session.commit()

    node1 = version.add_node(session, data={"key": "value1"})
    node2 = version.add_node(session, data={"key": "value2"})
    assert node1.id is not None
    assert node2.id is not None

    edge = version.add_edge(session, node1.id, node2.id, data={"relation": "connected"})
    assert edge.id is not None

#  Test for creating and restoring tags
def test_create_and_restore_tag(session):
    tree = Tree(name="Tag Restore Test Tree")
    session.add(tree)
    session.commit()

    # Create initial version
    version1 = TreeVersion(tree_id=tree.id, tag="v1.0", description="Initial version")
    session.add(version1)
    session.commit()

    # Create a tag for this version
    tag = "release-v1.0"
    tree.create_tag(session, tag=tag, description="First stable release")

    # Verify the tag is created successfully
    tree_versions = session.exec(select(TreeVersion).filter(TreeVersion.tree_id == tree.id)).all()
    print(f"\nTree Versions after Tagging: {len(tree_versions)} versions found")
    for version in tree_versions:
        print(f"Version {version.tag}: {version.description} - Created at {version.created_at}")

    # Restore from the tagged version
    print(f"\nRestoring from tag '{tag}'...")
    restored_version = tree.restore_from_tag(session, tag="release-v1.0")
    
    # Debugging: Print restored version details
    if restored_version:
        print(f"Restored Version: {restored_version.tag}, {restored_version.description}")
    else:
        print(f"Failed to restore version from tag '{tag}'.")

    # Check if the correct version is restored
    assert restored_version is not None, f"Restored version should not be None for tag '{tag}'"
    assert restored_version.tag == "release-v1.0", f"Expected restored version tag 'release-v1.0', got '{restored_version.tag}'"
    assert restored_version.description == "First stable release", f"Expected restored version description 'First stable release', got '{restored_version.description}'"

    # Ensure the version is not duplicated or incorrectly created during restore
    restored_version_recheck = session.get(TreeVersion, restored_version.id)
    assert restored_version_recheck is not None, "Restored version should be present in the database after restore"
    assert restored_version_recheck.tag == "release-v1.0", f"Restored version tag mismatch, expected 'release-v1.0', got '{restored_version_recheck.tag}'"



#  Test for traversing the tree
def test_traversal(session):
    tree = Tree(name="Tree Traversal Test")
    session.add(tree)
    session.commit()

    version = TreeVersion(tree_id=tree.id, tag="v1.0", description="Test traversal")
    session.add(version)
    session.commit()

    node1 = version.add_node(session, data={"setting": "value1"})
    node2 = version.add_node(session, data={"setting": "value2"})
    version.add_edge(session, node1.id, node2.id, data={"type": "dependency"})

    print("\nStarting Traversal from node 1:")
    def traverse_tree(node_id):
        node = session.get(TreeNode, node_id)
        print(f"Node {node.id}: {node.data}")
        stmt = select(TreeEdge).filter(TreeEdge.incoming_node_id == node.id)
        edges = session.exec(stmt).all()  # Using session.exec() instead of session.query()
        for edge in edges:
            print(f"Edge {edge.id}: {edge.data}")
            traverse_tree(edge.outgoing_node_id)

    traverse_tree(node1.id)

#  Test for finding a path between two nodes
def test_find_path(session):
    tree = Tree(name="Pathfinding Test Tree")
    session.add(tree)
    session.commit()

    version = TreeVersion(tree_id=tree.id, tag="v1.0", description="Test pathfinding")
    session.add(version)
    session.commit()

    node1 = version.add_node(session, data={"setting": "value1"})
    node2 = version.add_node(session, data={"setting": "value2"})
    node3 = version.add_node(session, data={"setting": "value3"})
    version.add_edge(session, node1.id, node2.id, data={"type": "dependency"})
    version.add_edge(session, node2.id, node3.id, data={"type": "path"})

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


if __name__ == "__main__":
    with Session(test_engine) as session:
        print("\nRunning Tests...")
        run_test("Create Tree and Version", test_create_tree_and_version, session)
        run_test("Create Multiple Versions", test_create_multiple_versions, session)
        run_test("Add Nodes and Edges", test_add_nodes_and_edges, session)
        run_test("Create and Restore Tag", test_create_and_restore_tag, session)
        run_test("Tree Traversal", test_traversal, session)
        run_test("Find Path", test_find_path, session)
