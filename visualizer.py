import os
import zlib
import argparse
from collections import deque
import datetime

class Commit:
    def __init__(self, commit_hash, parents, author_date):
        self.commit_hash = commit_hash
        self.parents = parents  # list of parent commit hashes
        self.author_date = author_date  # Unix timestamp

def parse_git_object(repo_path, object_hash):
    object_path = os.path.join(repo_path, '.git', 'objects', object_hash[:2], object_hash[2:])
    if not os.path.exists(object_path):
        raise Exception(f"Object {object_hash} not found.")
    with open(object_path, 'rb') as f:
        compressed_data = f.read()
    raw_data = zlib.decompress(compressed_data)
    header_end = raw_data.find(b'\x00')
    header = raw_data[:header_end]
    body = raw_data[header_end+1:]
    object_type, size = header.decode().split(' ')
    size = int(size)
    assert size == len(body)
    return object_type, body

def parse_commit(repo_path, commit_hash):
    object_type, data = parse_git_object(repo_path, commit_hash)
    assert object_type == 'commit'
    lines = data.decode().split('\n')
    parents = []
    author_date = None
    for line in lines:
        if line.startswith('parent '):
            parents.append(line[7:])
        elif line.startswith('author '):
            # parse author date
            parts = line.split()
            timestamp = int(parts[-2])
            # time_zone = parts[-1]
            author_date = timestamp
            break  # Usually author line is before the message
    if author_date is None:
        raise Exception(f"Author date not found for commit {commit_hash}")
    return Commit(commit_hash, parents, author_date)

def get_head_commit(repo_path):
    head_path = os.path.join(repo_path, '.git', 'HEAD')
    with open(head_path, 'r') as f:
        ref = f.read().strip()
    if ref.startswith('ref:'):
        ref_path = ref[5:]
        ref_file = os.path.join(repo_path, '.git', ref_path)
        with open(ref_file, 'r') as f:
            commit_hash = f.read().strip()
        return commit_hash
    else:
        # If HEAD is detached
        commit_hash = ref
        return commit_hash

def traverse_commits(repo_path, start_commit_hash):
    commits = {}
    visited = set()
    queue = deque([start_commit_hash])
    while queue:
        commit_hash = queue.popleft()
        if commit_hash in visited:
            continue
        visited.add(commit_hash)
        commit = parse_commit(repo_path, commit_hash)
        commits[commit_hash] = commit
        # Enqueue parent commits
        for parent_hash in commit.parents:
            if parent_hash not in visited:
                queue.append(parent_hash)
    return commits

def build_dependency_graph(commits):
    # Sort commits by author date
    sorted_commits = sorted(commits.values(), key=lambda c: c.author_date)
    return sorted_commits

def generate_mermaid_graph(commits):
    lines = ["graph TD"]
    commit_nodes = {}
    for idx, commit in enumerate(commits):
        # Create node label
        # Node IDs in Mermaid cannot start with numbers, so add prefix
        node_id = f"_{commit.commit_hash[:6]}"
        # Use commit hash and date in the label
        dt = datetime.datetime.utcfromtimestamp(commit.author_date).strftime('%Y-%m-%d %H:%M:%S')
        label = f"{commit.commit_hash[:6]}\\n{dt}"
        commit_nodes[commit.commit_hash] = node_id
        lines.append(f'{node_id}["{label}"];')
    # Now add edges
    for commit in commits:
        node_id = commit_nodes[commit.commit_hash]
        for parent_hash in commit.parents:
            parent_node_id = commit_nodes.get(parent_hash)
            if parent_node_id:
                lines.append(f"{node_id} --> {parent_node_id};")
    return '\n'.join(lines)

def main():
    parser = argparse.ArgumentParser(description='Git Repository Visualizer')
    parser.add_argument('repo_path', help='Path to the repository to analyze')
    parser.add_argument('output_file', help='Path to the output file')
    args = parser.parse_args()

    repo_path = args.repo_path
    output_file = args.output_file

    head_commit_hash = get_head_commit(repo_path)
    commits_dict = traverse_commits(repo_path, head_commit_hash)
    sorted_commits = build_dependency_graph(commits_dict)
    mermaid_code = generate_mermaid_graph(sorted_commits)

    with open(output_file, 'w') as f:
        f.write(mermaid_code)

if __name__ == '__main__':
    main()