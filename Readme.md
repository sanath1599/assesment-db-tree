### Features
- Versioning and Tagging: Create multiple versions of a tree, tag them with meaningful names (e.g., v1.0, release-v1.0), and restore a tree to any tagged version.
- Node and Edge Management: Add nodes to tree versions, define relationships between them with edges, and navigate through the tree.
- Tree Traversal: Traverse the tree starting from any node and explore its connected nodes and edges.
- Pathfinding: Find paths between any two nodes in the tree using depth-first search (DFS).

###Project Structure 
`tree-versioning-system/`
`├── models.py          # Contains the data models for the tree, nodes, edges, and versions`
`├── interactive_test.py.py            # Main script to interact with the system (for creating trees, versions, etc.)`
`├── tests.py           # Unit and integration tests`
`├── example.py.py           # Sample file to create data`
`├── requirements.txt   # Project dependencies`
`├──README.md          # Project documentation (you are here!)`


### Setup
#### Clone Repo
```git clone https://github.com/sanath1599/assesment-db-tree.git ```
```cd assesment-db-tree```

#### INstall Dependencies
```pip install -r requirements.txt```

### Design Decisions & Tradeoffs

### Usage
####Create and Version a Tree
```python
from models import Tree, TreeVersion, Session, create_engine

# Initialize the database engine
sqlite_url = "sqlite:///kastle.db"
engine = create_engine(sqlite_url)

# Create a new tree and version
with Session(engine) as session:
    tree = Tree(name="Test Tree")
    session.add(tree)
    session.commit()

    version = TreeVersion(tree_id=tree.id, tag="v1.0", description="Initial version")
    session.add(version)
    session.commit()

```
#### Create a Tag for a Tree Version
```python
tree.create_tag(session, tag="release-v1.0", description="First stable release")

```

#### Restore a Tree from the Tag
```python
restored_version = tree.restore_from_tag(session, tag="release-v1.0")

```
#### Add nodes and edges to the tree 
```python
node1 = version.add_node(session, data={"setting": "value1"})
node2 = version.add_node(session, data={"setting": "value2"})
version.add_edge(session, node1.id, node2.id, data={"relation": "dependency"})
```

#### TRaversing a tree
```python
def traverse_tree(node_id):
    node = session.get(TreeNode, node_id)
    print(f"Node {node.id}: {node.data}")
    stmt = select(TreeEdge).filter(TreeEdge.incoming_node_id == node.id)
    edges = session.exec(stmt).all()
    for edge in edges:
        print(f"Edge {edge.id}: {edge.data}")
        traverse_tree(edge.outgoing_node_id)

```

#### Find a path between two given nodes
```python
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

```