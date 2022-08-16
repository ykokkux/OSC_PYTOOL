import pexpect
import sys
import pdb
import re
import pprint
import json

from ast import literal_eval


class PytoolMenuBasedWrapper:
    """
    PytoolMenuBasedWrapper class contains different methods that are used to
    configure various ports with different specifications
    """

    def __init__(self, lekpath, bitstream):
        self.lekpath = lekpath
        self.bitstream = bitstream
        self.pytool_session = self.launch_pytool()

    def launch_pytool(self):
        """
        This method is used to launch the Pytool session in soc
        :return: swan id pytool_session
        """
        try:
            self.pytool_session = pexpect.spawn(
                f"python3 {self.lekpath}cli/pytool/management_config/config.py --lekpath "
                f"{self.lekpath} --bitstream {self.bitstream}")
            self.pytool_session.logfile = sys.stdout.buffer
            self.pytool_session.expect("==>")
            return self.pytool_session
        except pexpect.exceptions.EOF:
            print(
                "Login failed. Login error: {}".format(
                    self.pytool_session.before.decode())
            )
            sys.exit()
        except pexpect.exceptions.TIMEOUT as pexpect_timeout:
            print(
                "Timed out waiting for string {!r} in stream:{} ".format(
                    str(pexpect_timeout), self.pytool_session.before.decode()))
            sys.exit(1)

    def _parse_menu_config(self, output):
        """
        This method is used to parse the menu based output from pytool
        :param output: It contains the output that needs to be parsed
        :type output: str
        :return: menu_dict
        """
        menu_dict = {}
        op = output.split('\n')
        for v in op[0:]:
            if v.find(')') != -1:
                res = v.split(')', 1)
                menu_dict[res[-1].strip()] = res[0].strip()
        pprint.PrettyPrinter().pprint(menu_dict)
        if "Not a Valid Choice Try again" in output:
            # This error statement has to go to json file
            print("entered an invalid choice")
        return menu_dict

    def configure_host_or_soc_port(self, port_type, port):
        """
        This method is used to configure both the host port and soc port
        :param port_type: Type of port to be configured (host/soc)
        :type port_type: str
        :param port: It contains the port value that needs to be configured
        :type port: int
        :return: swan id pytool_session
        """
        result = False
        output = self.pytool_session.before.decode()
        menu_dict = self._parse_menu_config(str(output))
        if len(menu_dict) != 0:
            self.pytool_session.sendline(
                menu_dict[f'Configure {port_type} Port'])
            self.pytool_session.expect(
                "Enable and Configure Host|SOC Port from range "
                "0-\d+ \(or \"b\" to Back/Previous Menu\) :")
            self.pytool_session.sendline(str(port))
            self.pytool_session.expect("==>")
            output1 = self.pytool_session.before.decode()
            result = True
        # save and apply cannot be added for individual config of host or soc
        return result, output1

    def configure_mtu_size(self, port_dict, port_type, imt="off", quit=False):
        """
        This method is used to configure the mtu size for the ports
        :param port_dict: This param contains the port no and mtu values for that port
        :type port_dict: dict
        :param port_type: Type of port to be configured (host/soc)
        :type port_type: str
        :param imt: This parm is specific to enable/disable imt in soc
        :type imt: str
        :param quit: This parm is used to select either need to quit
        from pytool or to stay in the pytool
        :type quit: True/False
        :return: swan id pytool_session
        """
        result_list = []
        for port, mtu in port_dict.items():
            _, output = obj.configure_host_or_soc_port(port_type, port)
            menu_dict1 = obj._parse_menu_config(str(output))
            if len(menu_dict1) != 0:
                result_list.append(True)
                self.pytool_session.sendline(menu_dict1["Modify MTU"])
                self.pytool_session.expect(
                    "Enter the mtu \(or \"b\" to Back/Previous Menu\) :")
                self.pytool_session.sendline(str(mtu))
                self.pytool_session.expect("Main Menu")
                if port_type == "SOC":
                    if imt == "on":
                        output = self.pytool_session.before.decode()
                        menu_dict2 = self._parse_menu_config(str(output))
                        if len(menu_dict2) != 0:
                            result_list.append(True)
                            self.pytool_session.sendline(
                                menu_dict2["Enable/Disable IMT Status"])
                            self.pytool_session.expect(
                                "Do you want to toggle\? \(y/n/b\)")
                            self.pytool_session.sendline('y')
                            self.pytool_session.expect("Main Menu\r\n==>")
                output2 = self.pytool_session.before.decode()
                menu_dict3 = obj._parse_menu_config(str(output2))
                if len(menu_dict3) != 0:
                    result_list.append(True)
                    self.pytool_session.sendline(
                        menu_dict3["Back/Previous Menu"])
                    self.pytool_session.expect(
                        "Enable and Configure Host|SOC Port from"
                        " range 0-\d+ \(or \"b\" to Back/Previous Menu\) :")
                    self.pytool_session.sendline("b")
                    self.pytool_session.expect("==>")
                    output3 = self.pytool_session.before.decode()
        self.save_and_apply(output3)
        if quit:
            self.quit()
        return True if False not in result_list else False

    def port_mapping(self, port_map_dict, quit=False):
        result_list = []
        _, output = obj.configure_host_or_soc_port(port_type="Host", port=1)
        menu_dict = obj._parse_menu_config(str(output))
        if len(menu_dict) != 0:
            result_list.append(True)
            self.pytool_session.sendline(menu_dict["Back/Previous Menu"])
            self.pytool_session.expect(
                "Enable and Configure Host|SOC Port from "
                "range 0-\d+ \(or \"b\" to Back/Previous Menu\) :")
            self.pytool_session.sendline("b")
            self.pytool_session.expect("==>")
            output1 = self.pytool_session.before.decode()
            menu_dict1 = obj._parse_menu_config(str(output1))
            if len(menu_dict1) != 0:
                result_list.append(True)
                self.pytool_session.sendline(menu_dict1["Mapping"])
                self.pytool_session.expect("==>")
                output2 = self.pytool_session.before.decode()
                menu_dict2 = self._parse_menu_config(str(output2))
                if len(menu_dict2) != 0:
                    result_list.append(True)
                    for port_map_type, port in port_map_dict.items():
                        for src_port, dst_port in port.items():
                            self.pytool_session.sendline(
                                menu_dict2[
                                    f"Port  Mapping({port_map_type})"])
                            self.pytool_session.expect(
                                "Enter Host|SOC Port from range 0-\d+ "
                                "\(or \"b\" to Back/Previous Menu\) :")
                            self.pytool_session.sendline(str(src_port))
                            if port_map_type != "SOC  PF to Line":
                                self.pytool_session.expect(
                                    "Enter Host|SOC Port from range 0-\d+ "
                                    "\(or \"b\" to Back/Previous Menu\) :")
                                self.pytool_session.sendline(str(dst_port))
                            self.pytool_session.expect("==>")
        output3 = self.pytool_session.before.decode()
        menu_dict3 = self._parse_menu_config(str(output3))
        if len(menu_dict3) != 0:
            result_list.append(True)
            self.pytool_session.sendline(menu_dict3["Back/Previous Menu"])
            self.pytool_session.expect("==>")
            output4 = self.pytool_session.before.decode()
            self.save_and_apply(output4)
        if quit:
            self.quit()
        return True if False not in result_list else False

    def save_and_apply(self, menu_op):
        """
        This method is used to save and apply the configurations
        :param menu_op: It is a menu that provides shortcuts for actions
        :type menu_op: str
        :return: swan id pytool_session
        """
        result_list = []
        menu_dict1 = self._parse_menu_config(str(menu_op))
        if len(menu_dict1) != 0:
            result_list.append(True)
            self.pytool_session.sendline(
                menu_dict1["Save Configuration to file"])
            self.pytool_session.expect("==>")
            output4 = self.pytool_session.before.decode()
            menu_dict2 = self._parse_menu_config(str(output4))
            if len(menu_dict2) != 0:
                result_list.append(True)
                self.pytool_session.sendline(menu_dict2["\x1b[31mApply (Changes to be applied)\x1b[0m"])
                self.pytool_session.expect("==>")
        return True if False not in result_list else False

    def quit(self):
        """
        This method is used to quit from pytool session
        :return: swan id pytool_session
        """
        result = False
        output = self.pytool_session.before.decode()
        menu_dict1 = obj._parse_menu_config(str(output))
        if len(menu_dict1) != 0:
            result = True
            self.pytool_session.sendline(menu_dict1["Exit/Quit"])
            self.pytool_session.expect("Save latest Configuration\? \(y/n/b\)")
            self.pytool_session.sendline("y")
            self.pytool_session.expect("Goodbye")
        return result

'''
if __name__ == "__main__":
    obj = PytoolMenuBasedWrapper(
        lekpath="/root/networking.ethernet.acceleration.crystal-spring-canyon.platform/common/",
        bitstream=1)
    host_dict = {1: 2000, 2: 2000}
    soc_dict = {1: 2000, 2: 2000}
    obj.configure_mtu_size(port_dict=host_dict, port_type="Host", quit=False)
    obj.configure_mtu_size(port_dict=soc_dict, port_type="SOC", quit=False)
    obj.port_mapping(port_map_dict={"Host PF to SOC  PF": {1: 1, 2: 2},
                                    "SOC  PF to Host PF": {1: 1, 2: 2}}, quit=True)
'''


if __name__ == "__main__":
    with open(sys.argv[3]) as a:
        json_parameters = json.load(a)
    with open(sys.argv[4]) as b:
        error_info = json.load(b)
    main_tag = sys.argv[1]
    obj = PytoolMenuBasedWrapper(
                 lekpath=json_parameters["sample_json"]["pytool_parameteres"]["lek_path"],
                 bitstream=json_parameters["sample_json"]["pytool_parameteres"]["bitstream"])
    if main_tag == "MTU":
        op = obj.configure_mtu_size(port_dict=json_parameters["sample_json"][
            "MTU"]
                               ['port_list_host'], port_type=json_parameters[
                                "sample_json"]["MTU"]['port_type1'], quit=False)
        obj.configure_mtu_size(port_dict=json_parameters["sample_json"]["MTU"]
                               ['port_list_soc'], port_type=json_parameters[
                                "sample_json"]["MTU"]['port_type2'], quit=False)
        obj.port_mapping(json_parameters["sample_json"]["port_mapping"],
                         quit=True)
        if not op:
            print(error_info["error_info"]["error_msg1"])
