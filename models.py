from datetime import datetime
from sqlmodel import SQLModel, Field, create_engine, Session, Relationship
from typing import Optional, List
from sqlalchemy import JSON, Column

class Tree(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    versions: List["TreeVersion"] = Relationship(back_populates="tree", sa_relationship_kwargs={"cascade": "all, delete-orphan"})

    def get_latest_version(self, session: Session):
        return session.query(TreeVersion).filter_by(tree_id=self.id).order_by(TreeVersion.created_at.desc()).first()

    def get_version_by_tag(self, session: Session, tag: str):
        return session.query(TreeVersion).filter_by(tree_id=self.id, tag=tag).first()

    def create_tag(self, session: Session, tag: str, description: str):
        latest = self.get_latest_version(session)
        if not latest:
            raise ValueError("No versions exist to tag.")
        return latest.create_new_version(session, tag=tag, description=description)

    def create_new_tree_version_from_tag(self, session: Session, tag: str):
        version = self.get_version_by_tag(session, tag)
        if not version:
            raise ValueError(f"No version with tag {tag} found")
        return version.create_new_version(session, tag=None, description=f"New version from tag {tag}")

    def restore_from_tag(self, session: Session, tag: str):
        version = self.get_version_by_tag(session, tag)
        if not version:
            raise ValueError(f"No version with tag {tag} found")
        return version.create_new_version(session, tag=None, description=f"Restored version from tag {tag}")

    def get_root_nodes(self, session: Session):
        return session.query(TreeNode).filter_by(tree_id=self.id, parent_version_id=None).all()

    def get_by_tag(self, session: Session, tag: str):
        return session.query(Tree).join(TreeVersion).filter(TreeVersion.tag == tag).first()


class TreeVersion(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    tree_id: int = Field(foreign_key="tree.id")
    parent_version_id: Optional[int] = Field(foreign_key="treeversion.id", default=None)
    tag: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    tag_created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)  # Added tag_created_at

    tree: "Tree" = Relationship(back_populates="versions")
    nodes: List["TreeNode"] = Relationship(back_populates="version", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    edges: List["TreeEdge"] = Relationship(back_populates="version", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    parent: Optional["TreeVersion"] = Relationship(sa_relationship_kwargs={"remote_side": "TreeVersion.id"})

    def create_new_version(self, session: Session, tag: Optional[str] = None, description: Optional[str] = None):
        new_version = TreeVersion(tree_id=self.tree_id, parent_version_id=self.id, tag=tag, description=description)
        session.add(new_version)
        session.flush()  
        old_to_new_node = {}
        for node in self.nodes:
            new_node = TreeNode(tree_version_id=new_version.id, data=node.data)
            session.add(new_node)
            session.flush()
            old_to_new_node[node.id] = new_node.id

        for edge in self.edges:
            new_edge = TreeEdge(
                tree_version_id=new_version.id,
                incoming_node_id=old_to_new_node[edge.incoming_node_id],
                outgoing_node_id=old_to_new_node[edge.outgoing_node_id],
                data=edge.data
            )
            session.add(new_edge)

        session.commit()
        return new_version

    def add_node(self, session: Session, data: dict):  # Updated to use dict (JSON)
        new_node = TreeNode(tree_version_id=self.id, data=data)
        session.add(new_node)
        session.commit()
        return new_node

    def add_edge(self, session: Session, node_id_1: int, node_id_2: int, data: dict):  # Updated to use dict (JSON)
        node1 = session.get(TreeNode, node_id_1)
        node2 = session.get(TreeNode, node_id_2)
        if not node1 or not node2:
            raise ValueError("One or both nodes do not exist in this version")
        new_edge = TreeEdge(tree_version_id=self.id, incoming_node_id=node1.id, outgoing_node_id=node2.id, data=data)
        session.add(new_edge)
        session.commit()
        return new_edge

    def get_child_nodes(self, session: Session):
        return session.query(TreeNode).join(TreeEdge).filter(TreeEdge.incoming_node_id == self.id).all()

    def get_parent_nodes(self, session: Session):
        return session.query(TreeNode).join(TreeEdge).filter(TreeEdge.outgoing_node_id == self.id).all()


class TreeNode(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    tree_version_id: int = Field(foreign_key="treeversion.id")
    data: dict = Field(sa_column=Column(JSON))  # Corrected to use Column with JSON
    created_at: datetime = Field(default_factory=datetime.utcnow)

    version: "TreeVersion" = Relationship(back_populates="nodes")


class TreeEdge(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    tree_version_id: int = Field(foreign_key="treeversion.id")
    incoming_node_id: int = Field(foreign_key="treenode.id")
    outgoing_node_id: int = Field(foreign_key="treenode.id")
    data: dict = Field(sa_column=Column(JSON))  # Corrected to use Column with JSON
    created_at: datetime = Field(default_factory=datetime.utcnow)

    version: "TreeVersion" = Relationship(back_populates="edges")


sqlite_url = "sqlite:///kastle.db"
engine = create_engine(sqlite_url)

def init_db():
    SQLModel.metadata.create_all(engine)

if __name__ == "__main__":
    init_db()
    print("Database and tables created successfully.")
