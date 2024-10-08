# filesystem.py

import time
import os
import re
import random
from datetime import datetime
import calendar

class File:
    def __init__(self, name, content=b'', permissions='rw-', owner='user'):
        self.name = name
        self.content = content
        self.size = len(content)
        self.created_at = time.time()
        self.modified_at = self.created_at
        self.parent = None
        self.permissions = permissions
        self.owner = owner

    def to_dict(self):
        return {
            'name': self.name,
            'content': self.content.decode('utf-8', errors='ignore'),
            'size': self.size,
            'created_at': self.created_at,
            'modified_at': self.modified_at,
            'permissions': self.permissions,
            'owner': self.owner,
        }

    @staticmethod
    def from_dict(data):
        file = File(
            data['name'],
            content=data['content'].encode('utf-8'),
            permissions=data.get('permissions', 'rw-'),
            owner=data.get('owner', 'user')
        )
        file.size = data['size']
        file.created_at = data['created_at']
        file.modified_at = data['modified_at']
        return file

class Directory:
    def __init__(self, name, permissions='rwx', owner='user'):
        self.name = name
        self.children = {}  # name -> File or Directory
        self.created_at = time.time()
        self.modified_at = self.created_at
        self.parent = None
        self.permissions = permissions
        self.owner = owner

    def to_dict(self):
        return {
            'name': self.name,
            'children': {
                name: child.to_dict() for name, child in self.children.items()
            },
            'created_at': self.created_at,
            'modified_at': self.modified_at,
            'permissions': self.permissions,
            'owner': self.owner,
        }

    @staticmethod
    def from_dict(data):
        dir = Directory(
            data['name'],
            permissions=data.get('permissions', 'rwx'),
            owner=data.get('owner', 'user')
        )
        dir.created_at = data['created_at']
        dir.modified_at = data['modified_at']
        for name, child_data in data['children'].items():
            if 'children' in child_data:
                # It's a directory
                child = Directory.from_dict(child_data)
            else:
                # It's a file
                child = File.from_dict(child_data)
            child.parent = dir
            dir.children[name] = child
        return dir

class FileSystem:
    def __init__(self):
        self.root = Directory('/')
        self.root.parent = None
        self.current_dir = self.root
        self.total_size = 0  # total size of all files
        self.max_size = 5 * 1024 * 1024  # 5MB
        self.hostname = "simfs"
        self.uptime_start = time.time()
        self.processes = [
            {'pid': 1, 'name': 'init'},
            {'pid': 2, 'name': 'bash'},
            {'pid': 3, 'name': 'python'},
            {'pid': 4, 'name': 'discord_bot'},
        ]

    def to_dict(self):
        return {
            'root': self.root.to_dict(),
            'current_path': self.get_current_path(),
            'total_size': self.total_size,
            'hostname': self.hostname,
            'uptime_start': self.uptime_start,
            'processes': self.processes,
        }

    def from_dict(self, data):
        self.root = Directory.from_dict(data['root'])
        self.current_dir = self.get_directory_by_path(data.get('current_path', '/'))
        self.total_size = data.get('total_size', 0)
        self.hostname = data.get('hostname', "simfs")
        self.uptime_start = data.get('uptime_start', time.time())
        self.processes = data.get('processes', [
            {'pid': 1, 'name': 'init'},
            {'pid': 2, 'name': 'bash'},
            {'pid': 3, 'name': 'python'},
            {'pid': 4, 'name': 'discord_bot'},
        ])

    def get_directory_by_path(self, path):
        if path == '/':
            return self.root
        parts = path.strip('/').split('/')
        dir = self.root
        for part in parts:
            if part in dir.children and isinstance(dir.children[part], Directory):
                dir = dir.children[part]
            else:
                return None
        return dir

    def resolve_path(self, path):
        if path.startswith('/'):
            dir = self.root
            parts = path.strip('/').split('/')
        else:
            dir = self.current_dir
            parts = path.strip().split('/')
        for part in parts:
            if part == '':
                continue
            elif part == '.':
                continue
            elif part == '..':
                if dir.parent:
                    dir = dir.parent
            else:
                if part in dir.children:
                    dir = dir.children[part]
                else:
                    return None
        return dir

    def get_current_path(self):
        path = ''
        dir = self.current_dir
        while dir != self.root and dir is not None:
            path = '/' + dir.name + path
            dir = dir.parent
        return '/' if path == '' else path

    def execute_command(self, command):
        # Parse the command and execute the corresponding method
        args = command.strip().split()
        if not args:
            return "No command entered."
        cmd = args[0]
        args = args[1:]

        if cmd == 'ls':
            return self.cmd_ls(args)
        elif cmd == 'cd':
            return self.cmd_cd(args)
        elif cmd == 'pwd':
            return self.cmd_pwd(args)
        elif cmd == 'mkdir':
            return self.cmd_mkdir(args)
        elif cmd == 'touch':
            return self.cmd_touch(args)
        elif cmd == 'rm':
            return self.cmd_rm(args)
        elif cmd == 'cat':
            return self.cmd_cat(args)
        elif cmd == 'echo':
            return self.cmd_echo(args)
        elif cmd == 'cp':
            return self.cmd_cp(args)
        elif cmd == 'mv':
            return self.cmd_mv(args)
        elif cmd == 'du':
            return self.cmd_du(args)
        elif cmd == 'df':
            return self.cmd_df(args)
        elif cmd == 'find':
            return self.cmd_find(args)
        elif cmd == 'grep':
            return self.cmd_grep(args)
        elif cmd == 'chmod':
            return self.cmd_chmod(args)
        elif cmd == 'chown':
            return self.cmd_chown(args)
        elif cmd == 'ps':
            return self.cmd_ps(args)
        elif cmd == 'kill':
            return self.cmd_kill(args)
        elif cmd == 'ping':
            return self.cmd_ping(args)
        elif cmd == 'uptime':
            return self.cmd_uptime(args)
        elif cmd == 'whoami':
            return self.cmd_whoami(args)
        elif cmd == 'hostname':
            return self.cmd_hostname(args)
        elif cmd == 'date':
            return self.cmd_date(args)
        elif cmd == 'cal':
            return self.cmd_cal(args)
        elif cmd == 'help':
            return self.cmd_help(args)
        else:
            return f"{cmd}: command not found"

    # Command methods

    def cmd_ls(self, args):
        entries = self.current_dir.children.keys()
        return '\n'.join(entries) if entries else 'No entries found.'

    def cmd_cd(self, args):
        if not args:
            return 'cd: missing operand'
        path = args[0]
        target_dir = self.resolve_path(path)
        if target_dir and isinstance(target_dir, Directory):
            self.current_dir = target_dir
            return ''
        else:
            return f"cd: {path}: No such directory"

    def cmd_pwd(self, args):
        return self.get_current_path()

    def cmd_mkdir(self, args):
        if not args:
            return 'mkdir: missing operand\nUsage: mkdir <directory_name>'
        path = args[0]
        dir_name = os.path.basename(path)
        parent_dir = self.resolve_path(os.path.dirname(path))
        if not parent_dir:
            return f"mkdir: cannot create directory '{path}': No such directory"
        if not isinstance(parent_dir, Directory):
            return f"mkdir: '{os.path.dirname(path)}' is not a directory"
        if dir_name in parent_dir.children:
            return f"mkdir: cannot create directory '{dir_name}': File exists"
        new_dir = Directory(dir_name)
        new_dir.parent = parent_dir
        parent_dir.children[dir_name] = new_dir
        parent_dir.modified_at = time.time()
        return f"Directory '{dir_name}' created successfully."

    def cmd_touch(self, args):
        if not args:
            return 'touch: missing file operand\nUsage: touch <file_name>'
        path = args[0]
        filename = os.path.basename(path)
        parent_dir = self.resolve_path(os.path.dirname(path))
        if not parent_dir:
            return f"touch: cannot touch '{path}': No such directory"
        if not isinstance(parent_dir, Directory):
            return f"touch: '{os.path.dirname(path)}' is not a directory"
        if filename in parent_dir.children:
            file = parent_dir.children[filename]
            file.modified_at = time.time()
            return f"File '{filename}' updated successfully."
        else:
            new_file = File(filename)
            new_file.parent = parent_dir
            parent_dir.children[filename] = new_file
            parent_dir.modified_at = time.time()
            return f"File '{filename}' created successfully."

    def cmd_rm(self, args):
        if not args:
            return 'rm: missing operand\nUsage: rm <file_or_directory>'
        path = args[0]
        parent_dir = self.resolve_path(os.path.dirname(path))
        name = os.path.basename(path)
        if not parent_dir:
            return f"rm: cannot remove '{path}': No such directory"
        if not isinstance(parent_dir, Directory):
            return f"rm: '{os.path.dirname(path)}' is not a directory"
        if name in parent_dir.children:
            item = parent_dir.children.pop(name)
            if isinstance(item, File):
                self.total_size -= item.size
            parent_dir.modified_at = time.time()
            return f"'{name}' has been removed."
        else:
            return f"rm: cannot remove '{name}': No such file or directory"

    def cmd_cat(self, args):
        if not args:
            return 'cat: missing file operand\nUsage: cat <file_name>'
        path = args[0]
        file = self.resolve_path(path)
        if not file:
            return f"cat: {path}: No such file"
        if isinstance(file, Directory):
            return f"cat: {path}: Is a directory"
        try:
            content = file.content.decode('utf-8', errors='ignore')
            return content if content else 'File is empty.'
        except UnicodeDecodeError:
            return f"cat: {path}: Binary file not supported"

    def cmd_echo(self, args):
        if not args:
            return ''
        output = ' '.join(args)
        return output

    def cmd_cp(self, args):
        if len(args) < 2:
            return "cp: missing file operands\nUsage: cp <source> <destination>"
        source = args[0]
        destination = args[1]
        src_file = self.resolve_path(source)
        dest_file = self.resolve_path(destination)
        if not src_file:
            return f"cp: cannot stat '{source}': No such file or directory"
        if isinstance(src_file, Directory):
            return "cp: -r not implemented for directories"
        parent_dir = self.resolve_path(os.path.dirname(destination))
        dest_name = os.path.basename(destination)
        if not parent_dir:
            return f"cp: cannot create regular file '{destination}': No such directory"
        if not isinstance(parent_dir, Directory):
            return f"cp: '{os.path.dirname(destination)}' is not a directory"
        if dest_name in parent_dir.children:
            return f"cp: cannot overwrite existing file '{destination}'"
        new_file = File(dest_name, src_file.content, permissions=src_file.permissions, owner=src_file.owner)
        new_file.parent = parent_dir
        parent_dir.children[dest_name] = new_file
        parent_dir.modified_at = time.time()
        return f"File '{source}' copied to '{destination}' successfully."

    def cmd_mv(self, args):
        if len(args) < 2:
            return "mv: missing file operands\nUsage: mv <source> <destination>"
        source = args[0]
        destination = args[1]
        src_item = self.resolve_path(source)
        if not src_item:
            return f"mv: cannot stat '{source}': No such file or directory"
        parent_src = src_item.parent
        if not parent_src:
            return f"mv: cannot move root directory"
        parent_dest = self.resolve_path(os.path.dirname(destination))
        dest_name = os.path.basename(destination)
        if not parent_dest:
            return f"mv: cannot move to '{destination}': No such directory"
        if not isinstance(parent_dest, Directory):
            return f"mv: '{os.path.dirname(destination)}' is not a directory"
        if dest_name in parent_dest.children:
            return f"mv: cannot overwrite existing item '{destination}'"
        # Remove from source
        del parent_src.children[src_item.name]
        parent_src.modified_at = time.time()
        # Add to destination
        src_item.name = dest_name
        src_item.parent = parent_dest
        parent_dest.children[dest_name] = src_item
        parent_dest.modified_at = time.time()
        return f"'{source}' moved to '{destination}' successfully."

    def cmd_du(self, args):
        def get_size(directory):
            size = 0
            for child in directory.children.values():
                if isinstance(child, File):
                    size += child.size
                elif isinstance(child, Directory):
                    size += get_size(child)
            return size

        if not args:
            target_dir = self.current_dir
        else:
            path = args[0]
            target_dir = self.resolve_path(path)
            if not target_dir or not isinstance(target_dir, Directory):
                return f"du: cannot access '{path}': No such directory"

        size = get_size(target_dir)
        return f"{size // 1024}KB\t{self.get_current_path()}"

    def cmd_df(self, args):
        used = self.total_size
        free = self.max_size - used
        return (
            "Filesystem      Size   Used   Avail\n"
            f"/dev/simfs      5MB    {used // 1024}KB    {free // 1024}KB"
        )

    def cmd_find(self, args):
        if len(args) < 2:
            return "find: missing search path and name\nUsage: find <path> <name>"
        path = args[0]
        name = args[1]
        start_dir = self.resolve_path(path)
        if not start_dir or not isinstance(start_dir, Directory):
            return f"find: '{path}': No such directory"

        found = []

        def search(directory, current_path):
            for child in directory.children.values():
                child_path = os.path.join(current_path, child.name)
                if child.name == name:
                    found.append(child_path)
                if isinstance(child, Directory):
                    search(child, child_path)

        search(start_dir, path.rstrip('/'))
        if found:
            return '\n'.join(found)
        else:
            return f"find: '{name}' not found in '{path}'"

    def cmd_grep(self, args):
        if len(args) < 2:
            return "grep: missing pattern or file\nUsage: grep <pattern> <file>"
        pattern = args[0]
        filepath = args[1]
        file = self.resolve_path(filepath)
        if not file:
            return f"grep: {filepath}: No such file"
        if isinstance(file, Directory):
            return f"grep: {filepath}: Is a directory"
        try:
            content = file.content.decode('utf-8', errors='ignore')
        except UnicodeDecodeError:
            return f"grep: {filepath}: Binary file not supported"
        lines = content.splitlines()
        matched = [line for line in lines if pattern in line]
        if matched:
            return '\n'.join(matched)
        else:
            return f"grep: pattern not found in {filepath}"

    def cmd_chmod(self, args):
        if len(args) < 2:
            return "chmod: missing operand\nUsage: chmod <permissions> <file>"
        permissions = args[0]
        filepath = args[1]
        if not re.match(r'^[rwx-]{3}$', permissions):
            return "chmod: invalid permissions format. Use three characters (e.g., rw-, r-x, etc.)"
        file = self.resolve_path(filepath)
        if not file:
            return f"chmod: cannot access '{filepath}': No such file or directory"
        file.permissions = permissions
        file.modified_at = time.time()
        return f"Permissions of '{filepath}' changed to '{permissions}'."

    def cmd_chown(self, args):
        if len(args) < 2:
            return "chown: missing operand\nUsage: chown <owner> <file>"
        owner = args[0]
        filepath = args[1]
        file = self.resolve_path(filepath)
        if not file:
            return f"chown: cannot access '{filepath}': No such file or directory"
        file.owner = owner
        file.modified_at = time.time()
        return f"Owner of '{filepath}' changed to '{owner}'."

    def cmd_ps(self, args):
        header = "PID\tNAME"
        lines = [header]
        for proc in self.processes:
            lines.append(f"{proc['pid']}\t{proc['name']}")
        return '\n'.join(lines) if self.processes else "No running processes."

    def cmd_kill(self, args):
        if not args:
            return "kill: missing PID\nUsage: kill <pid>"
        try:
            pid = int(args[0])
        except ValueError:
            return "kill: invalid PID"
        for proc in self.processes:
            if proc['pid'] == pid:
                self.processes.remove(proc)
                return f"Process {pid} ('{proc['name']}') terminated."
        return f"kill: cannot kill PID {pid}: No such process"

    def cmd_ping(self, args):
        if not args:
            return "ping: missing host\nUsage: ping <host>"
        host = args[0]
        response = f"Pinging {host} with 32 bytes of data:\n"
        for i in range(1, 5):
            response += f"Reply from {host}: bytes=32 time={random.randint(1, 100)}ms\n"
        response += (
            f"\nPing statistics for {host}:\n"
            f"    Packets: Sent = 4, Received = 4, Lost = 0 (0% loss),\n"
            f"Approximate round trip times in milli-seconds:\n"
            f"    Minimum = 1ms, Maximum = 100ms, Average = 50ms"
        )
        return response

    def cmd_uptime(self, args):
        uptime_seconds = int(time.time() - self.uptime_start)
        days, remainder = divmod(uptime_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"Uptime: {days} days, {hours} hours, {minutes} minutes, {seconds} seconds"

    def cmd_whoami(self, args):
        return "user"

    def cmd_hostname(self, args):
        return self.hostname

    def cmd_date(self, args):
        return datetime.now().strftime("%a %b %d %H:%M:%S %Z %Y")

    def cmd_cal(self, args):
        now = datetime.now()
        cal = calendar.month(now.year, now.month)
        return cal

    def cmd_help(self, args):
        commands = [
            'ls', 'cd', 'pwd', 'mkdir', 'touch', 'rm', 'cat', 'echo', 'cp', 'mv',
            'du', 'df', 'find', 'grep', 'chmod', 'chown', 'ps', 'kill', 'ping',
            'uptime', 'whoami', 'hostname', 'date', 'cal', 'help'
        ]
        return 'Available commands:\n' + '\n'.join(commands)

    def add_file(self, filename, content):
        if filename in self.current_dir.children:
            return False  # File already exists
        size = len(content)
        if self.total_size + size > self.max_size:
            return False  # Exceeds storage limit
        new_file = File(filename, content)
        new_file.parent = self.current_dir
        self.current_dir.children[filename] = new_file
        self.current_dir.modified_at = time.time()
        self.total_size += size
        return True