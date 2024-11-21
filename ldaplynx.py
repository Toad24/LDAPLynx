import os
import glob

try:
    import readline
except ImportError:
    import pyreadline as readline  # Use pyreadline3 on Windows

from colorama import Fore, Style


class LDIFConsole:
    def __init__(self):
        self.ldif_content = None
        self.membership_attributes = ["member", "memberUid"]
        self.nodes = []
        self.edges = []
        self.commands = [
            "help",
            "load",
            "set_attrs",
            "parse",
            "view_nodes",
            "view_edges",
            "view_group",
            "export",
            "exit"
        ]
        self.setup_tab_completion()

    def setup_tab_completion(self):
        """Setup tab completion for commands and file paths."""
        def completer(text, state):
            buffer = readline.get_line_buffer().strip()
            tokens = buffer.split()

            # If "load" command is being typed, complete file paths
            if buffer.startswith("load"):
                partial_path = buffer[5:].strip()  # Get the file path portion
                matches = glob.glob(partial_path + "*")  # Find matching files/directories
                matches = [m + ("/" if os.path.isdir(m) else "") for m in matches]  # Add "/" to directories
                if state < len(matches):
                    return matches[state]
                return None

            # Otherwise, complete commands
            if len(tokens) == 1:
                matches = [cmd for cmd in self.commands if cmd.startswith(text)]
                if state < len(matches):
                    return matches[state]
            return None

        readline.set_completer(completer)
        readline.parse_and_bind("tab: complete")

    def load_ldif(self, file_path):
        if not file_path:
            print(f"{Fore.YELLOW}Usage: load <file_path>{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Example: load demo_ldap_data.ldif{Style.RESET_ALL}")
            return

        try:
            with open(file_path, 'r') as file:
                self.ldif_content = file.read()
            print(f"{Fore.GREEN}LDIF file '{file_path}' loaded successfully.{Style.RESET_ALL}")

            # Auto-detect membership attributes
            detected_attributes = self.detect_membership_attributes()
            if detected_attributes:
                group_entries = self.get_group_entries(detected_attributes)
                print(f"\n{Fore.CYAN}Found {len(group_entries)} group(s) with membership attributes.{Style.RESET_ALL}")
                if group_entries:
                    group = group_entries[0]
                    group_name = group['dn']
                    member_lines = group['members']
                    print(f"{Fore.CYAN}Example group:{Style.RESET_ALL}")
                    print(f"  {Fore.MAGENTA}{group_name}{Style.RESET_ALL}")
                    print(f"  {Fore.MAGENTA}Members: {len(member_lines)}{Style.RESET_ALL}")
                if member_lines:
                    for idx, member in enumerate(member_lines):
                        if idx == 0 or idx < len(self.membership_attributes):
                            attr_display = self.membership_attributes[min(idx, len(self.membership_attributes) - 1)]
                            print(f"  {Fore.MAGENTA}Member Example ({attr_display}):{Style.RESET_ALL} {Fore.YELLOW}{member}{Style.RESET_ALL}")

                print(f"\n{Fore.CYAN}Detected membership attribute(s): {', '.join(detected_attributes)}{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}Do you want to use these attributes? (y/n){Style.RESET_ALL}")
                choice = input(f"> ").strip().lower()
                if choice == "y":
                    self.membership_attributes = detected_attributes
                else:
                    print(f"{Fore.YELLOW}Enter your preferred membership attributes (comma-separated):{Style.RESET_ALL}")
                    user_input = input(f"> ").strip()
                    self.membership_attributes = user_input.split(",")
            else:
                print(f"\n{Fore.YELLOW}No membership attributes detected.{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}Enter your preferred membership attributes (comma-separated):{Style.RESET_ALL}")
                user_input = input(f"> ").strip()
                self.membership_attributes = user_input.split(",")

            print(f"{Fore.GREEN}Using membership attribute(s): {', '.join(self.membership_attributes)}{Style.RESET_ALL}")
            print(f"{Fore.GREEN}Ready to parse.{Style.RESET_ALL}")
        except FileNotFoundError:
            print(f"{Fore.RED}Error: The file '{file_path}' does not exist.{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}An error occurred: {e}{Style.RESET_ALL}")

    def detect_membership_attributes(self):
        """Automatically detect likely membership attributes in the LDIF content."""
        if not self.ldif_content:
            return []

        common_attributes = ["member", "memberUid", "uniqueMember", "isMemberOf", "memberOf"]
        detected_attributes = set()

        for line in self.ldif_content.splitlines():
            line = line.strip()
            if ":" in line:
                attribute = line.split(":", 1)[0]
                if attribute in common_attributes:
                    detected_attributes.add(attribute)

        return list(detected_attributes)

    def get_group_entries(self, membership_attributes):
        """Get group entries containing the detected membership attributes."""
        group_entries = []
        current_entry = []
        current_dn = None
        members = []
        inside_group = False

        for line in self.ldif_content.splitlines():
            line = line.strip()
            if line.startswith("dn:"):
                if inside_group:
                    group_entries.append({"dn": current_dn, "members": members})
                current_entry = [line]
                current_dn = line.split(":", 1)[1].strip()
                members = []
                inside_group = False
            elif any(line.startswith(f"{attr}:") for attr in membership_attributes):
                inside_group = True
                members.append(line.split(":", 1)[1].strip())
            current_entry.append(line)

        if inside_group:
            group_entries.append({"dn": current_dn, "members": members})

        return group_entries

    def set_membership_attributes(self, attributes):
        if not attributes:
            print(f"{Fore.YELLOW}Usage: set_attrs <attributes>{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Example: set_attrs member,memberUid{Style.RESET_ALL}")
            return

        self.membership_attributes = attributes.split(",")
        print(f"{Fore.GREEN}Membership attributes set to: {', '.join(self.membership_attributes)}{Style.RESET_ALL}")

    def parse(self):
        if not self.ldif_content:
            print(f"{Fore.RED}No LDIF file loaded. Use the 'load' command first.{Style.RESET_ALL}")
            return

        self.nodes, self.edges = parse_ldif(self.ldif_content, self.membership_attributes)
        print(f"{Fore.GREEN}Parsed {len(self.nodes)} nodes and {len(self.edges)} edges. Ready for export.{Style.RESET_ALL}")

    def view_nodes(self):
        if not self.nodes:
            print(f"{Fore.RED}No nodes available. Run 'parse' first.{Style.RESET_ALL}")
            return
        print(f"{Fore.CYAN}Nodes:{Style.RESET_ALL}")
        for dn, label, type in self.nodes:
            print(f"  {Fore.BLUE}{type}: {label} ({dn}){Style.RESET_ALL}")

    def view_edges(self):
        if not self.edges:
            print(f"{Fore.RED}No edges available. Run 'parse' first.{Style.RESET_ALL}")
            return
        print(f"{Fore.CYAN}Edges:{Style.RESET_ALL}")
        for source, target, relation in self.edges:
            print(f"  {Fore.BLUE}{relation}: {source} -> {target}{Style.RESET_ALL}")

    def view_group(self, group_dn):
        if not self.ldif_content:
            print(f"{Fore.RED}No LDIF file loaded. Use the 'load' command first.{Style.RESET_ALL}")
            return

        group_found = False
        current_entry = []
        for line in self.ldif_content.splitlines():
            line = line.strip()
            if line.startswith("dn:"):
                if current_entry and current_entry[0].split(":", 1)[1].strip() == group_dn:
                    group_found = True
                    break
                current_entry = [line]
            else:
                current_entry.append(line)

        if current_entry and current_entry[0].split(":", 1)[1].strip() == group_dn:
            group_found = True

        if group_found:
            print(f"{Fore.CYAN}Group details for {group_dn}:{Style.RESET_ALL}")
            for line in current_entry:
                print(f"  {Fore.MAGENTA}{line}{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}Group '{group_dn}' not found.{Style.RESET_ALL}")

    def export(self, nodes_file="nodes.csv", edges_file="edges.csv"):
        if not self.nodes or not self.edges:
            print(f"{Fore.RED}No parsed data to export. Run 'parse' first.{Style.RESET_ALL}")
            return

        with open(nodes_file, "w") as nodes_file_obj:
            nodes_file_obj.write("Id,Label,Type\n")
            for dn, label, type in self.nodes:
                nodes_file_obj.write(f"\"{dn}\",\"{label}\",\"{type}\"\n")
        with open(edges_file, "w") as edges_file_obj:
            edges_file_obj.write("Source,Target,Relation\n")
            for source, target, relation in self.edges:
                edges_file_obj.write(f"\"{source}\",\"{target}\",\"{relation}\"\n")

        print(f"{Fore.GREEN}Files saved: '{nodes_file}' and '{edges_file}'{Style.RESET_ALL}")

    def help(self):
        print(f"""
{Fore.CYAN}
{Fore.YELLOW}Usage Instructions:{Style.RESET_ALL}
  1. {Fore.YELLOW}Load an LDIF file:{Style.RESET_ALL} Use 'load <file_path>' to load an LDIF file.
  2. {Fore.YELLOW}Parse the LDIF file:{Style.RESET_ALL} Use 'parse' to analyze the loaded data.
  3. {Fore.YELLOW}Export parsed data:{Style.RESET_ALL} Use 'export' to save nodes and edges to CSV files.

  {Fore.YELLOW}To generate an LDIF file:{Style.RESET_ALL} You can use the following command (assuming ldapsearch is installed):
  {Fore.YELLOW}ldapsearch -x -H <ldap_host> -b <search_base> > output.ldif{Style.RESET_ALL}
  {Fore.YELLOW}ldapsearch -x -H ldap://localhost -b dc=example,dc=com > output.ldif{Style.RESET_ALL}

  {Fore.YELLOW}load <file_path>{Style.RESET_ALL}     - Load an LDIF file (supports tab-completion for file paths).
  {Fore.YELLOW}set_attrs <attrs>{Style.RESET_ALL}    - Set membership attributes (comma-separated).
  {Fore.YELLOW}parse{Style.RESET_ALL}                - Parse the loaded LDIF file.
  {Fore.YELLOW}view_nodes{Style.RESET_ALL}           - View parsed nodes.
  {Fore.YELLOW}view_edges{Style.RESET_ALL}           - View parsed edges.
  {Fore.YELLOW}view_group <group_dn>{Style.RESET_ALL} - View details of a specific group by its DN.
  {Fore.YELLOW}export <nfile> <efile>{Style.RESET_ALL} - Export nodes and edges to CSV files (default: nodes.csv and edges.csv).
  {Fore.YELLOW}exit{Style.RESET_ALL}                 - Exit the console.
""")

    def run(self):
        print(rf"""
{Fore.GREEN}
$$\       $$$$$$$\   $$$$$$\  $$$$$$$\  $$\                                    
$$ |      $$  __$$\ $$  __$$\ $$  __$$\ $$ |                                   
$$ |      $$ |  $$ |$$ /  $$ |$$ |  $$ |$$ |     $$\   $$\ $$$$$$$\  $$\   $$\      /\_/\
$$ |      $$ |  $$ |$$$$$$$$ |$$$$$$$  |$$ |     $$ |  $$ |$$  __$$\ \$$\ $$  |    ( o.o )
$$ |      $$ |  $$ |$$  __$$ |$$  ____/ $$ |     $$ |  $$ |$$ |  $$ | \$$$$  /      > ^ <
$$ |      $$ |  $$ |$$ |  $$ |$$ |      $$ |     $$ |  $$ |$$ |  $$ | $$  $$<  
$$$$$$$$\ $$$$$$$  |$$ |  $$ |$$ |      $$$$$$$$\$$$$$$$ |$$ |  $$ |$$  /\$$\ 
\________|\_______/ \__|  \__|\__|      \________|\____$$ |\__|  \__|\__/  \__|
                                                 $$\   $$ |                    
                                                 \$$$$$$  |                    
                                                  \______/                     

LDAPLynx Console - Type 'help' for a list of commands.
{Style.RESET_ALL}""")
        while True:
            command = input(f"{Fore.CYAN}LDAPLynx> {Style.RESET_ALL}").strip()
            if not command:
                continue
            cmd_parts = command.split(" ", 1)
            cmd = cmd_parts[0]
            args = cmd_parts[1] if len(cmd_parts) > 1 else None

            if cmd == "help":
                self.help()
            elif cmd == "load":
                self.load_ldif(args)
            elif cmd == "set_attrs":
                self.set_membership_attributes(args)
            elif cmd == "parse":
                self.parse()
            elif cmd == "view_nodes":
                self.view_nodes()
            elif cmd == "view_edges":
                self.view_edges()
            elif cmd == "view_group":
                if args:
                    self.view_group(args)
                else:
                    print(f"{Fore.RED}Usage: view_group <group_dn>{Style.RESET_ALL}")
            elif cmd == "export":
                if args:
                    files = args.split()
                    if len(files) == 2:
                        self.export(files[0], files[1])
                    else:
                        print(f"{Fore.RED}Usage: export <nodes_file> <edges_file>{Style.RESET_ALL}")
                else:
                    self.export()
            elif cmd == "exit":
                print(f"{Fore.GREEN}Exiting LDAPLynx Console.{Style.RESET_ALL}")
                break
            else:
                print(f"{Fore.RED}Unknown command: {cmd}. Type 'help' for a list of commands.{Style.RESET_ALL}")

def parse_ldif(ldif_content, membership_attributes):
    uid_to_dn = {}  # Maps user UIDs to their full DNs
    edges = []
    nodes = set()

    current_dn = None
    current_type = None
    for line in ldif_content.splitlines():
        line = line.strip()
        if line.startswith("dn:"):
            current_dn = line.split(":", 1)[1].strip()
            current_type = None
        elif line.startswith("objectClass:"):
            if "inetOrgPerson" in line or "posixAccount" in line:
                current_type = "User"
            elif "groupOfNames" in line or "posixGroup" in line or "groupOfMembers" in line:
                current_type = "Group"
        elif line.startswith("uid:") and current_type == "User":
            uid = line.split(":", 1)[1].strip()
            nodes.add((current_dn, uid, current_type))
        elif line.startswith("cn:") and current_type == "Group":
            cn = line.split(":", 1)[1].strip()
            nodes.add((current_dn, cn, current_type))
        else:
            for attr in membership_attributes:
                if line.startswith(f"{attr}:"):
                    member_value = line.split(":", 1)[1].strip()
                    if attr == "memberUid":
                        member_dn = uid_to_dn.get(member_value, None)
                    else:
                        member_dn = member_value
                    if member_dn:
                        edges.append((member_dn, current_dn, "memberOf"))

    return list(nodes), edges


if __name__ == "__main__":
    console = LDIFConsole()
    console.run()
