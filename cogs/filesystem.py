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
        self.history = []  # Store the command history
        self.environment = {}  # Environment variables
        self.aliases = {}  # Command aliases

    def to_dict(self):
        return {
            'root': self.root.to_dict(),
            'current_path': self.get_current_path(),
            'total_size': self.total_size,
            'hostname': self.hostname,
            'uptime_start': self.uptime_start,
            'processes': self.processes,
            'history': self.history,
            'environment': self.environment,
            'aliases': self.aliases,
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
        self.history = data.get('history', [])
        self.environment = data.get('environment', {})
        self.aliases = data.get('aliases', {})

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
        self.history.append(command)
        cmd_line = command.strip()
        if not cmd_line:
            return "No command entered."
        args = cmd_line.split()
        if not args:
            return "No command entered."
        cmd = args[0]
        args = args[1:]

        # Check for aliases
        if cmd in self.aliases:
            alias_cmd = self.aliases[cmd]
            # Recursively execute the alias command with the remaining args
            new_command = alias_cmd + ' ' + ' '.join(args)
            return self.execute_command(new_command)

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
        elif cmd == 'download':
            return self.cmd_download(args)
        elif cmd == 'help':
            return self.cmd_help(args)
        elif cmd == 'head':
            return self.cmd_head(args)
        elif cmd == 'tail':
            return self.cmd_tail(args)
        elif cmd == 'sort':
            return self.cmd_sort(args)
        elif cmd == 'uniq':
            return self.cmd_uniq(args)
        elif cmd == 'wc':
            return self.cmd_wc(args)
        elif cmd == 'sleep':
            return self.cmd_sleep(args)
        elif cmd == 'basename':
            return self.cmd_basename(args)
        elif cmd == 'dirname':
            return self.cmd_dirname(args)
        elif cmd == 'seq':
            return self.cmd_seq(args)
        elif cmd == 'factor':
            return self.cmd_factor(args)
        elif cmd == 'yes':
            return self.cmd_yes(args)
        elif cmd == 'rev':
            return self.cmd_rev(args)
        elif cmd == 'rmdir':
            return self.cmd_rmdir(args)
        elif cmd == 'ln':
            return self.cmd_ln(args)
        elif cmd == 'id':
            return self.cmd_id(args)
        elif cmd == 'history':
            return self.cmd_history(args)
        elif cmd == 'export':
            return self.cmd_export(args)
        elif cmd == 'env':
            return self.cmd_env(args)
        elif cmd == 'alias':
            return self.cmd_alias(args)
        elif cmd == 'unalias':
            return self.cmd_unalias(args)
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
        return ''

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
            return ''
        else:
            new_file = File(filename)
            new_file.parent = parent_dir
            parent_dir.children[filename] = new_file
            parent_dir.modified_at = time.time()
            return ''

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
            return ''
        else:
            return f"rm: cannot remove '{name}': No such file or directory"

    def cmd_rmdir(self, args):
        if not args:
            return 'rmdir: missing operand\nUsage: rmdir <directory>'
        path = args[0]
        dir = self.resolve_path(path)
        if not dir:
            return f"rmdir: failed to remove '{path}': No such directory"
        if not isinstance(dir, Directory):
            return f"rmdir: failed to remove '{path}': Not a directory"
        if dir.children:
            return f"rmdir: failed to remove '{path}': Directory not empty"
        parent_dir = dir.parent
        if parent_dir:
            del parent_dir.children[dir.name]
            parent_dir.modified_at = time.time()
            return ''
        else:
            return "rmdir: cannot remove root directory"

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
            return content if content else ''
        except UnicodeDecodeError:
            return f"cat: {path}: Binary file not supported"

    def cmd_head(self, args):
        if not args:
            return 'head: missing file operand\nUsage: head <file_name>'
        path = args[0]
        file = self.resolve_path(path)
        if not file:
            return f"head: cannot open '{path}' for reading: No such file or directory"
        if isinstance(file, Directory):
            return f"head: error reading '{path}': Is a directory"
        try:
            content = file.content.decode('utf-8', errors='ignore')
            lines = content.splitlines()
            head_lines = lines[:10]
            return '\n'.join(head_lines) if head_lines else ''
        except UnicodeDecodeError:
            return f"head: {path}: Binary file not supported"

    def cmd_tail(self, args):
        if not args:
            return 'tail: missing file operand\nUsage: tail <file_name>'
        path = args[0]
        file = self.resolve_path(path)
        if not file:
            return f"tail: cannot open '{path}' for reading: No such file or directory"
        if isinstance(file, Directory):
            return f"tail: error reading '{path}': Is a directory"
        try:
            content = file.content.decode('utf-8', errors='ignore')
            lines = content.splitlines()
            tail_lines = lines[-10:]
            return '\n'.join(tail_lines) if tail_lines else ''
        except UnicodeDecodeError:
            return f"tail: {path}: Binary file not supported"

    def cmd_sort(self, args):
        if not args:
            return 'sort: missing file operand\nUsage: sort <file_name>'
        path = args[0]
        file = self.resolve_path(path)
        if not file:
            return f"sort: cannot read: '{path}': No such file or directory"
        if isinstance(file, Directory):
            return f"sort: read failed '{path}': Is a directory"
        try:
            content = file.content.decode('utf-8', errors='ignore')
            lines = content.splitlines()
            lines.sort()
            return '\n'.join(lines) if lines else ''
        except UnicodeDecodeError:
            return f"sort: {path}: Binary file not supported"

    def cmd_uniq(self, args):
        if not args:
            return 'uniq: missing file operand\nUsage: uniq <file_name>'
        path = args[0]
        file = self.resolve_path(path)
        if not file:
            return f"uniq: {path}: No such file or directory"
        if isinstance(file, Directory):
            return f"uniq: {path}: Is a directory"
        try:
            content = file.content.decode('utf-8', errors='ignore')
            lines = content.splitlines()
            unique_lines = []
            previous_line = None
            for line in lines:
                if line != previous_line:
                    unique_lines.append(line)
                    previous_line = line
            return '\n'.join(unique_lines) if unique_lines else ''
        except UnicodeDecodeError:
            return f"uniq: {path}: Binary file not supported"

    def cmd_wc(self, args):
        if not args:
            return 'wc: missing file operand\nUsage: wc <file_name>'
        path = args[0]
        file = self.resolve_path(path)
        if not file:
            return f"wc: {path}: No such file or directory"
        if isinstance(file, Directory):
            return f"wc: {path}: Is a directory"
        try:
            content = file.content.decode('utf-8', errors='ignore')
            lines = content.splitlines()
            words = content.split()
            chars = len(content)
            return f"{len(lines)} {len(words)} {chars} {path}"
        except UnicodeDecodeError:
            return f"wc: {path}: Binary file not supported"

    def cmd_download(self, args):
        if not args:
            return 'download: missing file operand\nUsage: download <file_name>'
        path = args[0]
        file = self.resolve_path(path)
        if not file:
            return f"download: {path}: No such file"
        if isinstance(file, Directory):
            return f"download: {path}: Is a directory"
        return (path, file.content)

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
        return ''

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
        return ''

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
        return ''

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
        return ''

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
                return ''
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

    def cmd_who(self, args):
        return "user"

    def cmd_id(self, args):
        return 'uid=1000(user) gid=1000(user) groups=1000(user)'

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
            'ls', 'cd', 'pwd', 'mkdir', 'touch', 'rm', 'rmdir', 'cat', 'echo', 'cp', 'mv',
            'du', 'df', 'find', 'grep', 'chmod', 'chown', 'ps', 'kill', 'ping',
            'uptime', 'whoami', 'who', 'id', 'hostname', 'date', 'cal', 'help', 'download',
            'head', 'tail', 'sort', 'uniq', 'wc', 'sleep', 'basename', 'dirname',
            'seq', 'factor', 'yes', 'rev', 'ln', 'history', 'export', 'env', 'alias', 'unalias'
        ]
        return 'Available commands:\n' + '\n'.join(commands)

    def cmd_sleep(self, args):
        if not args:
            return 'sleep: missing operand\nUsage: sleep <seconds>'
        try:
            seconds = float(args[0])
            if seconds < 0:
                return 'sleep: time cannot be negative'
            return f"Sleep for {seconds} seconds (simulated)"
        except ValueError:
            return 'sleep: invalid time interval'

    def cmd_basename(self, args):
        if not args:
            return 'basename: missing operand\nUsage: basename <path>'
        path = args[0]
        return os.path.basename(path)

    def cmd_dirname(self, args):
        if not args:
            return 'dirname: missing operand\nUsage: dirname <path>'
        path = args[0]
        return os.path.dirname(path)

    def cmd_seq(self, args):
        if not args:
            return 'seq: missing operand\nUsage: seq <number>'
        try:
            num = int(args[0])
            if num < 1:
                return 'seq: number must be greater than 0'
            return '\n'.join(str(i) for i in range(1, num+1))
        except ValueError:
            return 'seq: invalid number'

    def cmd_factor(self, args):
        if not args:
            return 'factor: missing operand\nUsage: factor <number>'
        try:
            num = int(args[0])
            if num < 1:
                return 'factor: number must be positive integer'
            factors = []
            i = 2
            original_num = num
            while i * i <= num:
                if num % i:
                    i += 1
                else:
                    num //= i
                    factors.append(str(i))
            if num > 1:
                factors.append(str(num))
            return f"{original_num}: {' '.join(factors)}"
        except ValueError:
            return 'factor: invalid number'

    def cmd_yes(self, args):
        output = 'y\n' * 10
        return output.strip()

    def cmd_rev(self, args):
        if not args:
            return 'rev: missing file operand\nUsage: rev <file_name>'
        path = args[0]
        file = self.resolve_path(path)
        if not file:
            return f"rev: {path}: No such file or directory"
        if isinstance(file, Directory):
            return f"rev: {path}: Is a directory"
        try:
            content = file.content.decode('utf-8', errors='ignore')
            reversed_content = '\n'.join(line[::-1] for line in content.splitlines())
            return reversed_content if reversed_content else ''
        except UnicodeDecodeError:
            return f"rev: {path}: Binary file not supported"

    def cmd_ln(self, args):
        if len(args) < 2:
            return "ln: missing file operands\nUsage: ln <source> <link_name>"
        source = args[0]
        link_name = args[1]
        src_file = self.resolve_path(source)
        if not src_file:
            return f"ln: failed to access '{source}': No such file or directory"
        if isinstance(src_file, Directory):
            return "ln: hard link not allowed for directory"
        parent_dir = self.resolve_path(os.path.dirname(link_name))
        link_basename = os.path.basename(link_name)
        if not parent_dir:
            return f"ln: failed to create hard link '{link_name}': No such directory"
        if not isinstance(parent_dir, Directory):
            return f"ln: '{os.path.dirname(link_name)}' is not a directory"
        if link_basename in parent_dir.children:
            return f"ln: failed to create hard link '{link_name}': File exists"
        parent_dir.children[link_basename] = src_file
        parent_dir.modified_at = time.time()
        return ''

    def cmd_history(self, args):
        output = ''
        for i, cmd in enumerate(self.history[-10:], start=1):
            output += f"{i} {cmd}\n"
        return output.strip() if output else "No history available."

    def cmd_export(self, args):
        if not args:
            return 'export: missing operand\nUsage: export VAR=value'
        assignment = args[0]
        if '=' not in assignment:
            return 'export: invalid format. Use VAR=value'
        var, value = assignment.split('=', 1)
        self.environment[var] = value
        return ''

    def cmd_env(self, args):
        if self.environment:
            return '\n'.join(f"{key}={value}" for key, value in self.environment.items())
        else:
            return ''

    def cmd_alias(self, args):
        if not args:
            if self.aliases:
                return '\n'.join(f"alias {k}='{v}'" for k, v in self.aliases.items())
            else:
                return ''
        else:
            assignment = ' '.join(args)
            if '=' not in assignment:
                return 'alias: invalid format. Use alias name=\'command\''
            name, command = assignment.split('=', 1)
            command = command.strip("'\"")
            self.aliases[name.strip()] = command.strip()
            return ''

    def cmd_unalias(self, args):
        if not args:
            return 'unalias: missing operand\nUsage: unalias name'
        name = args[0]
        if name in self.aliases:
            del self.aliases[name]
            return ''
        else:
            return f'unalias: {name}: not found'

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
