# filesystem.py

import time
import os

class File:
    def __init__(self, name, content=b''):
        self.name = name
        self.content = content
        self.size = len(content)
        self.created_at = time.time()
        self.modified_at = self.created_at
        self.parent = None

    def to_dict(self):
        return {
            'name': self.name,
            'content': self.content.decode('utf-8', errors='ignore'),
            'size': self.size,
            'created_at': self.created_at,
            'modified_at': self.modified_at,
        }

    @staticmethod
    def from_dict(data):
        file = File(data['name'], content=data['content'].encode('utf-8'))
        file.size = data['size']
        file.created_at = data['created_at']
        file.modified_at = data['modified_at']
        return file

class Directory:
    def __init__(self, name):
        self.name = name
        self.children = {}  # name -> File or Directory
        self.created_at = time.time()
        self.modified_at = self.created_at
        self.parent = None

    def to_dict(self):
        return {
            'name': self.name,
            'children': {
                name: child.to_dict() for name, child in self.children.items()
            },
            'created_at': self.created_at,
            'modified_at': self.modified_at,
        }

    @staticmethod
    def from_dict(data):
        dir = Directory(data['name'])
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

    def to_dict(self):
        return {
            'root': self.root.to_dict(),
            'current_path': self.get_current_path(),
            'total_size': self.total_size,
        }

    def from_dict(self, data):
        self.root = Directory.from_dict(data['root'])
        self.current_dir = self.get_directory_by_path(data['current_path'])
        self.total_size = data['total_size']

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
            return ''
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
        return '\n'.join(entries) if entries else ''

    def cmd_cd(self, args):
        if not args:
            return ''
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
            return 'mkdir: missing operand'
        path = args[0]
        dir_name = os.path.basename(path)
        parent_dir = self.resolve_path(os.path.dirname(path))
        if parent_dir and isinstance(parent_dir, Directory):
            if dir_name in parent_dir.children:
                return f"mkdir: cannot create directory '{dir_name}': File exists"
            else:
                new_dir = Directory(dir_name)
                new_dir.parent = parent_dir
                parent_dir.children[dir_name] = new_dir
                parent_dir.modified_at = time.time()
                return ''
        else:
            return f"mkdir: cannot create directory '{dir_name}': No such file or directory"

    def cmd_touch(self, args):
        if not args:
            return 'touch: missing file operand'
        path = args[0]
        filename = os.path.basename(path)
        parent_dir = self.resolve_path(os.path.dirname(path))
        if parent_dir and isinstance(parent_dir, Directory):
            if filename in parent_dir.children:
                file = parent_dir.children[filename]
                file.modified_at = time.time()
                return ''
            else:
                new_file = File(filename)
                new_file.parent = parent_dir
                parent_dir.children[filename] = new_file
                parent_dir.modified_at = time.time()
                return ''
        else:
            return f"touch: cannot touch '{filename}': No such file or directory"

    def cmd_rm(self, args):
        if not args:
            return 'rm: missing operand'
        path = args[0]
        parent_dir = self.resolve_path(os.path.dirname(path))
        name = os.path.basename(path)
        if parent_dir and isinstance(parent_dir, Directory):
            if name in parent_dir.children:
                item = parent_dir.children.pop(name)
                if isinstance(item, File):
                    self.total_size -= item.size
                parent_dir.modified_at = time.time()
                return ''
            else:
                return f"rm: cannot remove '{name}': No such file or directory"
        else:
            return f"rm: cannot remove '{name}': No such file or directory"

    def cmd_cat(self, args):
        if not args:
            return 'cat: missing file operand'
        path = args[0]
        file = self.resolve_path(path)
        if file and isinstance(file, File):
            return file.content.decode('utf-8', errors='ignore')
        else:
            return f"cat: {path}: No such file"

    def cmd_echo(self, args):
        if not args:
            return ''
        output = ' '.join(args)
        return output

    def cmd_df(self, args):
        used = self.total_size
        free = self.max_size - used
        return (
            "Filesystem      Size   Used   Avail\n"
            f"/dev/simfs      5MB    {used // 1024}KB    {free // 1024}KB"
        )

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

    # Additional command methods can be implemented similarly

    # Placeholder methods for other commands
    def cmd_cp(self, args):
        return "cp: Command not implemented yet."

    def cmd_mv(self, args):
        return "mv: Command not implemented yet."

    def cmd_du(self, args):
        return "du: Command not implemented yet."

    def cmd_find(self, args):
        return "find: Command not implemented yet."

    def cmd_grep(self, args):
        return "grep: Command not implemented yet."

    def cmd_chmod(self, args):
        return "chmod: Command not implemented yet."

    def cmd_chown(self, args):
        return "chown: Command not implemented yet."

    def cmd_ps(self, args):
        return "ps: Command not implemented yet."

    def cmd_kill(self, args):
        return "kill: Command not implemented yet."

    def cmd_ping(self, args):
        return "ping: Command not implemented yet."

    def cmd_uptime(self, args):
        return "uptime: Command not implemented yet."

    def cmd_whoami(self, args):
        return "whoami: Command not implemented yet."

    def cmd_hostname(self, args):
        return "hostname: Command not implemented yet."

    def cmd_date(self, args):
        return "date: Command not implemented yet."

    def cmd_cal(self, args):
        return "cal: Command not implemented yet."
