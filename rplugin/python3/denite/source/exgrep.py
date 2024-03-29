from .base import Base
import subprocess
import denite.util
import re
import os


def run_command(command, cwd, encode='utf8'):
    try:
        process = subprocess.run(command,
                                 cwd=cwd,
                                 stdout=subprocess.PIPE)

        return process.stdout.decode(encode).split('\n')
    except Exception as e:
        return []

def cmd_exists(cmd):
    return subprocess.call("type " + cmd, shell=True,
             stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0


class Source(Base):

    def __init__(self, vim):
        super().__init__(vim)
        self.vim = vim
        self.name = 'exgrep'
        self.kind = 'file'
        self.cnt = 0
        self.done = True

    def on_init(self, context):
        context['is_interactive'] = True

    def on_close(self, context):
        pass

    def get_args_rg(self, inputs):
        args = ['rg', '-S', '--vimgrep', '--no-heading', inputs,]
        return args

    def get_args_ag(self, inputs):
        args = ['ag', '-S', '--vimgrep', inputs,]
        return args

    def get_args_ack(self, inputs):
        args = ['ack', '-H', '-S', '--nopager', '--nocolor' '--nogroup', '--column', inputs,]
        return args

    def get_args_git(self, inputs):
        args = ['git', '--no-pager', 'grep', '-n', '--no-color', '-i', inputs, ]
        return args

    def get_args(self, inputs):
        if cmd_exists("rg"):
            return self.get_args_rg(inputs)
        elif cmd_exists("ag"):
            return self.get_args_ag(inputs)
        elif cmd_exists("ack"):
            return self.get_args_ack(inputs)
        elif cmd_exists("git"):
            return self.get_args_ack(inputs)


    def gather_candidates(self, context):
        if not self.done:
            return []

        # self.cnt += 1
        # self.vim.command('echo "cnt:' + str(self.cnt) + '"')
        inputs = context["input"].strip()
        kws = re.split('\s', inputs)

        if inputs == "" or len(kws) < 1:
            return [{'word': 'Please input keyword'}]

        # self.vim.command('echo "len:' + str(len(kws[0])) + '"')
        if len(kws[0]) <= 2:
            return [{'word': inputs, 'abbr': 'Please input at least 3 chars'}]

        self.done = False

        args = self.get_args(kws[0])
        output = run_command(args, os.getcwd())

        self.done = True

        rows = []
        for line in output:
            format = self.__candidate(line)
            if format is not None:
                rows.append(format)

        return rows

    def __candidate(self, line):
        try:
            regex = re.compile("\:\d+\:")
            path = regex.split(line)[0]
            body = ''.join(line.split(':')[2::])
            row = regex.search(line)[0].strip(':')

            return {
                'word': body,
                "abbr": '{0}:{1}: {2}'.format(
                    path,
                    row,
                    body
                ),
                'action__path': path,
                'action__line': int(row),
                'action__col': 0,
                'action__text': body
            }
        except TypeError:
            return None
