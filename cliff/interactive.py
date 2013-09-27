"""Application base class.
"""

import cmd
import itertools
import logging
import logging.handlers
import readline
import shlex


LOG = logging.getLogger(__name__)


class InteractiveApp(cmd.Cmd):
    """Provides "interactive mode" features.

    Refer to the cmd_ documentation for details about subclassing and
    configuring this class.

    .. _cmd: http://docs.python.org/library/cmd.html

    :param parent_app: The calling application (expected to be derived
                       from :class:`cliff.main.App`).
    :param command_manager: A :class:`cliff.commandmanager.CommandManager`
                            instance.
    :param stdin: Standard input stream
    :param stdout: Standard output stream

    """

    use_rawinput = True
    doc_header = "Shell commands (type help <topic>):"
    app_cmd_header = "Application commands (type help <topic>):"

    def __init__(self, parent_app, command_manager, stdin, stdout):
        self.parent_app = parent_app
        self.prompt = '(%s) ' % parent_app.NAME
        self.command_manager = command_manager
        cmd.Cmd.__init__(self, 'tab', stdin=stdin, stdout=stdout)
        # readline uses libedit under OS X, so it needs to be
        # configured differently.
        if 'libedit' in readline.__doc__:
            # emacs key bindings
            readline.parse_and_bind("bind -e")
            # tab completion
            readline.parse_and_bind("bind ^I rl_complete")
        else:
            readline.parse_and_bind("tab: complete")

    def default(self, line):
        # Tie in the the default command processor to
        # dispatch commands known to the command manager.
        # We send the message through our parent app,
        # since it already has the logic for executing
        # the subcommand.
        line_parts = shlex.split(line)
        self.parent_app.run_subcommand(line_parts)

    def help_help(self):
        # Use the command manager to get instructions for "help"
        self.default('help help')

    def _plugin_command_names(self):
        return sorted(
            n
            for n, v in self.command_manager
            # Ignore the help command, because we have a builtin for
            # that and we don't want it to show up twice.
            if n != 'help'
        )

    def do_help(self, arg):
        """print help for a subcommand
        """
        if arg:
            # Check if the arg is a builtin command or something
            # coming from the command manager
            arg_parts = shlex.split(arg)
            method_name = '_'.join(
                itertools.chain(
                    ['do'],
                    itertools.takewhile(lambda x: not x.startswith('-'),
                                        arg_parts)
                )
            )
            # Have the command manager version of the help
            # command produce the help text since cmd and
            # cmd2 do not provide help for "help"
            if hasattr(self, method_name):
                return cmd.Cmd.do_help(self, arg)
            # Dispatch to the underlying help command,
            # which knows how to provide help for extension
            # commands.
            self.default('help ' + arg)
        else:
            cmd.Cmd.do_help(self, arg)
            cmd_names = self._plugin_command_names()
            self.print_topics(self.app_cmd_header, cmd_names, 15, 80)
        return

    def do_EOF(self, line):
        """exit interactive mode
        """
        return True

    def completedefault(self, text, line, begidx, endidx):
        # Tab-completion for commands known to the command manager.
        # Does not handle options on the commands.
        completions = self.get_names()
        if text:
            completions = [n for n in completions
                           if n.startswith(text)
                           ]
        return completions

    def completenames(self, text, *ignored):
        """Return a list of candidate names based on the prefix text.
        """
        return [
            name for name in (
                (n[3:] if n.startswith('do_') else n)
                for n in self.get_names()
            )
            if name.startswith(text)
        ]

    def get_names(self):
        """Return a list of all command names.
        """
        # Override the base class version to include names from the
        # command manager.
        plugins = self._plugin_command_names()
        built_ins = [n
                     for n in cmd.Cmd.get_names(self)
                     # filter out things that look like they should be
                     # hidden from the user
                     if n.startswith('do_') and not n.startswith('do__')
                     ]
        return list(sorted(itertools.chain(plugins, built_ins)))

    # def precmd(self, statement):
    #     # Pre-process the parsed command in case it looks like one of
    #     # our subcommands, since cmd2 does not handle multi-part
    #     # command names by default.
    #     line_parts = shlex.split(statement)
    #     try:
    #         the_cmd = self.command_manager.find_command(line_parts)
    #         cmd_factory, cmd_name, sub_argv = the_cmd
    #     except ValueError:
    #         # Not a plugin command
    #         pass
    #     else:
    #         statement.parsed.command = cmd_name
    #         statement.parsed.args = ' '.join(sub_argv)
    #     return statement
