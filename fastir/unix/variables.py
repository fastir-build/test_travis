import re
import pwd


class HostVariables:
    def __init__(self):
        self.userprofiles = set()

        for pwdent in pwd.getpwall():
            self.userprofiles.add(pwdent.pw_dir)

    def substitute(self, path):
        paths = set()
        for userprofile in self.userprofiles:
            value = path
            for variable in ['%%users.homedir%%']:
                value = re.compile(re.escape(variable)).sub(userprofile, value)
            value = re.compile('/+').sub('/', value)
            paths.add(value)
        return paths


class UnixHostVariables(HostVariables):

    def init_variables(self):
        userprofiles = set()

        for pwdent in pwd.getpwall():
            userprofiles.add(pwdent.pw_dir)

        self.add_variable('%%users.homedir%%', userprofiles)
